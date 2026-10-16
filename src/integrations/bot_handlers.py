import os
from pathlib import Path
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from sqlalchemy import text

# Import database connection & functions
from src.core.db.database import AsyncSessionLocal
from src.core.db.handlegoal import (
    save_roadmaps,
    save_phase_overview_of_road_map,
    get_current_phase,
    get_next_week_number,
    save_phase_task_of_phase_overview,
    save_task_of_phase_task,
    check_can_create_next_week,
)

# Import models & services
from src.core.models.RoadMap import PhaseOverview, RoadmapOverview
from src.core.models.Task import PhaseTaskSchedule
from src.core.generations import Generation
from src.integrations.service import GoogleTask
from src.integrations.states import GoalSetupState

load_dotenv()
router = Router()

API_KEY = os.getenv("GEMINI_API_KEY")
llm_service = Generation(api_key=API_KEY)

BASE_PATH = Path(__file__).resolve().parent.parent.parent
CREDENTIALS_FILE = BASE_PATH / "config" / "credentials.json"
TOKEN_FILE = BASE_PATH / "config" / "token.json"
SCOPES = ['https://www.googleapis.com/auth/tasks']


# --- HELPER: FORMAT TIN NHẮN XEM TRƯỚC SPRINT ---
def render_sprint_preview(sprint_schedule: PhaseTaskSchedule, phase_num: int) -> tuple[str, InlineKeyboardMarkup]:
    task_lines = [
        f"📅 <b>DỰ THẢO SPRINT 7 NGÀY - PHASE {phase_num} (Tuần {sprint_schedule.week_number})</b>",
        "<b>Danh sách công việc dự kiến:</b>"
    ]

    for idx, t in enumerate(sprint_schedule.tasks, start=1):
        start_str = t.calendar_start.strftime("%H:%M") if hasattr(t.calendar_start, "strftime") else str(t.calendar_start)[11:16]
        end_str = t.calendar_end.strftime("%H:%M") if hasattr(t.calendar_end, "strftime") else str(t.calendar_end)[11:16]
        due_str = str(t.google_task_due)[:10]

        task_lines.append(
            f"{idx}. <b>{t.title}</b>"
            f"\n   ⏰ {start_str} - {end_str} | Hạn: <code>{due_str}</code>"
            f"\n   📌 <i>Ghi chú: {t.notes or 'Không có'}</i>"
        )
    task_lines.append("\n💡 <i>Cuối tuần được để trống làm Buffer Day để dự phòng dời lịch khi cần.</i>")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 Đồng bộ Google Tasks & Lưu", callback_data="approve_sprint"),
            InlineKeyboardButton(text="❌ Hủy bỏ", callback_data="cancel_setup")
        ]
    ])
    return "\n".join(task_lines), keyboard


# --- 1. LỆNH BẮT ĐẦU ---
@router.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(GoalSetupState.waiting_for_goal)
    
    welcome_text = (
        f"Xin chào <b>{message.from_user.first_name}</b>! 👋\n\n"
        "Tôi là trợ lý AI quản lý mục tiêu cá nhân. Tôi sẽ giúp bạn:\n"
        "1. Phân rã mục tiêu thành lộ trình (Roadmap) bài bản.\n"
        "2. Lập Sprint 7 ngày (có ngày nghỉ đệm dự phòng).\n"
        "3. Tự động đồng bộ lên <b>Google Tasks</b> và cơ sở dữ liệu.\n\n"
        "👉 <i>Hãy nhập mục tiêu bạn muốn thực hiện (Ví dụ: 'Học lập trình Backend Python từ con số 0 trong 6 tháng'):</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML")


# --- 2. TIẾP NHẬN MỤC TIÊU & TẠO ROADMAP ---
@router.message(GoalSetupState.waiting_for_goal)
async def handle_goal_input(message: Message, state: FSMContext):
    user_goal = message.text.strip()
    wait_msg = await message.answer("⏳ Đang phân tích mục tiêu và thiết kế lộ trình...")

    try:
        roadmap = await llm_service.generateRoadmap(user_goal)
        
        await state.update_data(
            user_goal=user_goal,
            roadmap=roadmap.model_dump()
        )
        
        text_lines = [
            f"🎯 <b>MỤC TIÊU: {roadmap.goal_title.upper()}</b>",
            f"📝 <i>{roadmap.summary}</i>",
            f"⏳ Tổng thời gian dự kiến: <b>{roadmap.total_estimated_days} ngày</b>\n",
            "<b>Các giai đoạn thực hiện (Phases):</b>"
        ]
        
        for phase in roadmap.phase_task:
            text_lines.append(
                f"\n🔹 <b>Phase {phase.phase_number}: {phase.phase_title}</b> ({phase.duration_days} ngày)"
                f"\n  • Trọng tâm: {phase.phase_description}"
                f"\n  • Đầu ra: <code>{phase.key_outcome}</code>"
            )
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Duyệt & Khởi tạo Phase 1", callback_data="approve_roadmap"),
                InlineKeyboardButton(text="🔄 Soạn lại mục tiêu", callback_data="retry_goal")
            ]
        ])
        
        await wait_msg.delete()
        await message.answer("\n".join(text_lines), reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(GoalSetupState.waiting_roadmap_approval)

    except Exception as e:
        await wait_msg.edit_text(f"❌ Có lỗi xảy ra trong quá trình phân rã: {e}\nVui lòng thử lại!")


# --- 3. DUYỆT ROADMAP & TẠO SPRINT TUẦN 1 ---
@router.callback_query(GoalSetupState.waiting_roadmap_approval, F.data == "approve_roadmap")
async def handle_approve_roadmap(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=None)
    
    wait_msg = await query.message.answer("⚙️ Đang tạo TaskList trên Google, lưu dữ liệu và bẻ nhỏ task Phase 1...")

    try:
        data = await state.get_data()
        roadmap_dict = data.get("roadmap")
        if not roadmap_dict:
            await wait_msg.edit_text("❌ Không tìm thấy dữ liệu lộ trình. Vui lòng bắt đầu lại với /start!")
            return

        roadmap = RoadmapOverview.model_validate(roadmap_dict)

        # 1. Tạo Google TaskList
        google_service = await GoogleTask.create(
            credentials_file=str(CREDENTIALS_FILE), 
            token_file=str(TOKEN_FILE), 
            scopes=SCOPES
        )
        tasklist_title = f"🎯 {roadmap.goal_title}"
        google_tasklist_id = await google_service.create_task_list(title=tasklist_title)

        # 2. Lưu Roadmap (gắn với telegram user_id) và các Phase vào Database
        phase_overview_id_1 = None
        async with AsyncSessionLocal() as db_session:
            road_map_id = await save_roadmaps(
                db_session=db_session,
                roadmap=roadmap,
                google_tasklist_id=google_tasklist_id,
                user_id=query.from_user.id  # Đảm bảo truyền user_id
            )
            for phase in roadmap.phase_task:
                await save_phase_overview_of_road_map(
                    db_session=db_session,
                    road_map_id=road_map_id,
                    phase_overview=phase
                )
            
            current_phase_record = await get_current_phase(db_session=db_session, road_map_id=road_map_id)
            phase_overview_id_1 = current_phase_record["id"]

        # 3. Bẻ nhỏ Phase 1 thành Sprint Tuần 1
        phase_1 = roadmap.phase_task[0]
        sprint_schedule = await llm_service.generateTask(
            roadMapOvervieww=roadmap,
            target_phase_number=phase_1.phase_number,
            week_number=1,
            preferred_start_hour=19,
            daily_hours_limit=2.0
        )

        # 4. Cập nhật state
        await state.update_data(
            road_map_id=road_map_id,
            google_tasklist_id=google_tasklist_id,
            current_phase_number=phase_1.phase_number,
            phase_overview_id=phase_overview_id_1,
            sprint_schedule=sprint_schedule.model_dump()
        )

        # 5. Hiển thị preview
        msg_text, keyboard = render_sprint_preview(sprint_schedule, phase_1.phase_number)
        await wait_msg.delete()
        await query.message.answer(msg_text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(GoalSetupState.waiting_sprint_approval)

    except Exception as e:
        await wait_msg.edit_text(f"❌ Có lỗi xảy ra trong quá trình khởi tạo: {str(e)}")


# --- 4. CHỐT SPRINT & LƯU DB + ĐẨY GOOGLE TASKS ---
@router.callback_query(GoalSetupState.waiting_sprint_approval, F.data == "approve_sprint")
async def handle_approve_sprint(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=None)
    wait_msg = await query.message.answer("📡 Đang đồng bộ công việc lên Google Tasks & Database...")

    data = await state.get_data()
    sprint_data = data.get("sprint_schedule")
    google_tasklist_id = data.get("google_tasklist_id")
    phase_overview_id = data.get("phase_overview_id")
    road_map_id = data.get("road_map_id")

    # Fallback nếu thiếu google_tasklist_id từ state (do gọi từ next_week hoặc bot restart)
    if not google_tasklist_id and road_map_id:
        async with AsyncSessionLocal() as db_session:
            res = await db_session.execute(
                text("SELECT google_tasklist_id FROM road_map WHERE id = :id"),
                {"id": road_map_id}
            )
            google_tasklist_id = res.scalar()

    if not sprint_data or not google_tasklist_id:
        await wait_msg.edit_text("❌ Không tìm thấy thông tin sprint hoặc Google TaskList ID. Vui lòng thử lại!")
        return

    sprint_schedule = PhaseTaskSchedule.model_validate(sprint_data)

    try:
        # 1. Lưu phase_task và task con vào DB
        async with AsyncSessionLocal() as db_session:
            res = await db_session.execute(
                text("""
                    INSERT INTO phase_task (phase_number, week_number, week_start_date, phase_overview_id, is_completed, created_at)
                    VALUES (:phase_number, :week_number, :week_start_date, :phase_overview_id, FALSE, CURRENT_TIMESTAMP)
                    RETURNING id
                """),
                {
                    "phase_number": sprint_schedule.phase_number,
                    "week_number": sprint_schedule.week_number,
                    "week_start_date": sprint_schedule.week_start_date,
                    "phase_overview_id": phase_overview_id
                }
            )
            phase_task_id = res.scalar()
            await db_session.commit()

            for item in sprint_schedule.tasks:
                await save_task_of_phase_task(
                    db_session=db_session,
                    phase_task_id=phase_task_id,
                    executable_Task=item
                )

        # 2. Đẩy các task lên Google Tasks
        google_service = await GoogleTask.create(
            credentials_file=str(CREDENTIALS_FILE),
            token_file=str(TOKEN_FILE),
            scopes=SCOPES
        )
        await google_service.create_multiple_google_tasks(
            tasks=sprint_schedule.tasks,
            task_list_id=google_tasklist_id
        )

        await wait_msg.delete()
        success_text = (
            "🎉 <b>ĐỒNG BỘ THÀNH CÔNG!</b>\n\n"
            f"• Đã lưu các task của <b>Tuần {sprint_schedule.week_number}</b> vào hệ thống.\n"
            "• Đã tạo các đầu việc trên <b>Google Tasks</b>.\n\n"
            "📌 Khi làm xong tuần này, gõ <code>/next_week</code> để kiểm tra và nhận các công việc cho tuần tiếp theo!"
        )
        await query.message.answer(success_text, parse_mode="HTML")
        # Xóa dữ liệu sprint tạm nhưng vẫn giữ lại road_map_id và google_tasklist_id
        await state.update_data(sprint_schedule=None)
        await state.set_state(None)

    except Exception as e:
        await wait_msg.edit_text(f"❌ Quá trình đồng bộ thất bại: {e}")


# --- 5. LỆNH TẠO TUẦN TIẾP THEO (/next_week) ---
@router.message(Command("next_week"))
async def handle_next_week(message: Message, state: FSMContext):
    data = await state.get_data()
    road_map_id = data.get("road_map_id")
    user_id = message.from_user.id

    async with AsyncSessionLocal() as db_session:
        # Nếu FSM state rỗng, truy vấn roadmap theo user_id
        if not road_map_id:
            last_rm = await db_session.execute(
                text("SELECT id, google_tasklist_id FROM road_map WHERE user_id = :user_id ORDER BY id DESC LIMIT 1"),
                {"user_id": user_id}
            )
            rm_row = last_rm.mappings().first()
            if not rm_row:
                await message.answer("⚠️ Bạn chưa có lộ trình nào. Hãy gõ /start để tạo mới!")
                return
            road_map_id = rm_row["id"]
            await state.update_data(road_map_id=road_map_id, google_tasklist_id=rm_row["google_tasklist_id"])

        # Kiểm tra điều kiện tuần cũ
        can_create, last_task_id, msg = await check_can_create_next_week(db_session, road_map_id)

        if not can_create:
            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Xác nhận hoàn thành tuần này", callback_data=f"done_week_{last_task_id}")
            ]])
            await message.answer(
                f"⚠️ {msg}\n\nVui lòng bấm xác nhận bên dưới để hoàn tất tuần cũ trước khi sinh task mới:",
                reply_markup=kb
            )
            return

        await generate_and_preview_next_week(message, state, db_session, road_map_id)


# --- 6. XÁC NHẬN HOÀN THÀNH TUẦN VÀ TIẾP TỤC ---
@router.callback_query(F.data.startswith("done_week_"))
async def handle_complete_week(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=None)

    task_id = int(query.data.split("_")[-1])
    data = await state.get_data()
    road_map_id = data.get("road_map_id")

    async with AsyncSessionLocal() as db_session:
        # Đánh dấu tuần hiện tại hoàn thành
        await db_session.execute(
            text("UPDATE phase_task SET is_completed = TRUE WHERE id = :id"),
            {"id": task_id}
        )
        await db_session.commit()

        await query.message.answer("🎉 <b>Tuyệt vời! Bạn đã hoàn thành tuần này!</b>\nĐang chuẩn bị nội dung tuần mới...", parse_mode="HTML")
        await generate_and_preview_next_week(query.message, state, db_session, road_map_id)


# --- HÀM PHỤ TRỢ: SINH TASK TUẦN TIẾP THEO ---
async def generate_and_preview_next_week(message: Message, state: FSMContext, db_session, road_map_id: int):
    # 1. Lấy phase hiện tại đang chạy
    current_phase = await get_current_phase(db_session, road_map_id)
    if not current_phase:
        await message.answer("🎉 Chúc mừng! Bạn đã hoàn thành toàn bộ lộ trình!")
        return

    # 2. Tính số tuần tiếp theo
    total_weeks = (current_phase["duration_days"] + 6) // 7
    next_week = await get_next_week_number(db_session, road_map_id, current_phase["phase_number"])

    # 3. Nếu hết tuần của phase này -> Chuyển sang Phase kế tiếp
    if next_week > total_weeks:
        await db_session.execute(
            text("UPDATE phase_overview SET status = 'COMPLETED' WHERE id = :id"),
            {"id": current_phase["id"]}
        )
        next_phase_res = await db_session.execute(
            text("""
                UPDATE phase_overview
                SET status = 'IN_PROGRESS'
                WHERE id = (
                    SELECT id FROM phase_overview
                    WHERE road_map_id = :road_map_id AND phase_number > :curr_phase_num
                    ORDER BY phase_number ASC LIMIT 1
                )
                RETURNING id, phase_number, phase_title, phase_description, duration_days, key_outcome, status
            """),
            {"road_map_id": road_map_id, "curr_phase_num": current_phase["phase_number"]}
        )
        await db_session.commit()
        next_phase = next_phase_res.mappings().first()

        if not next_phase:
            await message.answer("🏆 <b>Chúc mừng bạn đã hoàn thành tất cả các Phase của mục tiêu!</b>", parse_mode="HTML")
            return

        current_phase = next_phase
        next_week = 1

    # 4. Lấy lại RoadmapOverview và google_tasklist_id
    rm_info = await db_session.execute(
        text("SELECT goal_title, summary, total_estimated_days, google_tasklist_id FROM road_map WHERE id = :id"), 
        {"id": road_map_id}
    )
    rm_data = rm_info.mappings().first()
    phases_info = await db_session.execute(
        text("SELECT phase_number, phase_title, phase_description, duration_days, key_outcome FROM phase_overview WHERE road_map_id = :id ORDER BY phase_number"), 
        {"id": road_map_id}
    )
    phases_list = phases_info.mappings().all()

    roadmap_obj = RoadmapOverview(
        goal_title=rm_data["goal_title"],
        summary=rm_data["summary"],
        total_estimated_days=rm_data["total_estimated_days"],
        phase_task=[PhaseOverview(**p) for p in phases_list]
    )

    # 5. Gọi Gemini sinh task tuần mới
    sprint_schedule = await llm_service.generateTask(
        roadMapOvervieww=roadmap_obj,
        target_phase_number=current_phase["phase_number"],
        week_number=next_week,
        preferred_start_hour=19,
        daily_hours_limit=2.0
    )

    # Lưu đầy đủ cả google_tasklist_id và phase_overview_id vào FSM data
    await state.update_data(
        road_map_id=road_map_id,
        google_tasklist_id=rm_data["google_tasklist_id"],
        phase_overview_id=current_phase["id"],
        current_phase_number=current_phase["phase_number"],
        sprint_schedule=sprint_schedule.model_dump()
    )

    # 6. Render preview và gửi cho người dùng
    msg_text, keyboard = render_sprint_preview(sprint_schedule, current_phase["phase_number"])
    await message.answer(msg_text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(GoalSetupState.waiting_sprint_approval)


# --- 7. HỦY / THỬ LẠI ---
@router.callback_query(F.data.in_(["retry_goal", "cancel_setup"]))
async def handle_cancel_or_retry(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(GoalSetupState.waiting_for_goal)
    await query.message.edit_text("Đã hủy bỏ thiết lập. Vui lòng nhập lại mục tiêu mới:")
    await query.answer()