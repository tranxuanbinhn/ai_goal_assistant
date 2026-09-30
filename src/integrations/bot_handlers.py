from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from src.core.generations import Generation
from src.integrations.states import GoalSetupState
import os
# Giả sử bạn import các schema và service đã có
# from models import RoadmapOverview, PhaseTaskSchedule
# from services import llm_service, google_service, db_service
load_dotenv()
router = Router()
API_KEY =os.getenv("GEMINI_API_KEY")
llm_service =  Generation(api_key=API_KEY)
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
        "3. Tự động đồng bộ lên <b>Google Tasks</b> và <b>Google Calendar</b>.\n\n"
        "👉 <i>Hãy nhập mục tiêu bạn muốn thực hiện (Ví dụ: 'Học để thi đỗ chứng chỉ AWS Cloud Practitioner trong 2 tháng'):</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML")


# --- 2. TIẾP NHẬN MỤC TIÊU & TẠO ROADMAP ---
@router.message(GoalSetupState.waiting_for_goal)
async def handle_goal_input(message: Message, state: FSMContext):
    user_goal = message.text.strip()
    wait_msg = await message.answer("⏳ Đang phân tích mục tiêu và thiết kế lộ trình...")

    try:
        # Gọi Gemini sinh RoadmapOverview
        
        roadmap = await llm_service.generateRoadmap(user_goal)
        
        # Lưu roadmap vào bộ nhớ tạm của FSM để dùng ở bước sau
        await state.update_data(
            user_goal=user_goal,
            roadmap=roadmap.model_dump()
        )
        
        # Xây dựng tin nhắn hiển thị trực quan
        text_lines = [
            f"🎯 <b>MỤC TIÊU: {roadmap.goal_title.upper()}</b>",
            f"📝 <i>{roadmap.summary}</i>",
            f"⏳ Tổng thời gian dự kiến: <b>{roadmap.total_estimated_days} ngày</b>\n",
            "<b>Các giai đoạn thực hiện (Phases):</b>"
        ]
        
        for phase in roadmap.phases:
            text_lines.append(
                f"\n🔹 <b>Phase {phase.phase_number}: {phase.phase_title}</b> ({phase.duration_days} ngày)"
                f"\n  • Trọng tâm: {phase.phase_description}"
                f"\n  • Đầu ra (DoD): <code>{phase.key_outcome}</code>"
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
    await query.message.edit_reply_markup(reply_markup=None) # Xóa nút bấm cũ
    wait_msg = await query.message.answer("⚙️ Đang khởi tạo TaskList trên Google và bẻ nhỏ task cho 7 ngày đầu...")

    data = await state.get_data()
    roadmap_data = data["roadmap"]
    
    # 1. Tạo Google TaskList và lưu Goal + Phase vào Database
    # tasklist_id = google_service.get_or_create_tasklist(service, roadmap_data['goal_title'])
    # goal_id = await db_service.save_goal_and_phases(query.from_user.id, roadmap_data, tasklist_id)
    tasklist_id = "mock_tasklist_id"
    goal_id = 1
    
    # 2. Gọi Gemini bẻ nhỏ Phase 1 thành Sprint 7 ngày
    phase_1 = roadmap_data["phases"][0]
    sprint_schedule = await llm_service.generateTask(
        roadmap_summary=roadmap_data,
        target_phase_number=phase_1["phase_number"],
        user_preferences={"preferred_start_hour": 19, "daily_hours_limit": 2.0}
    )
    
    # Lưu thông tin tạm
    await state.update_data(
        goal_id=goal_id,
        tasklist_id=tasklist_id,
        current_phase_number=1,
        sprint_schedule=sprint_schedule.model_dump()
    )
    
    # Định dạng tin nhắn hiển thị Task tuần
    task_lines = [
        f"📅 <b>DỰ THẢO SPRINT 7 NGÀY - PHASE 1 (Tuần {sprint_schedule.week_number})</b>",
        f"🎯 Mục tiêu tuần: <i>{sprint_schedule.key_outcome}</i>\n",
        "<b>Danh sách công việc dự kiến:</b>"
    ]
    
    for idx, t in enumerate(sprint_schedule.tasks, start=1):
        task_lines.append(
            f"{idx}. <b>{t.title}</b>"
            f"\n   ⏰ {t.calendar_start[11:16]} - {t.calendar_end[11:16]} | Hạn chót: <code>{t.google_task_due[:10]}</code>"
            f"\n   📌 <i>Ghi chú: {t.notes or 'Không có'}</i>"
        )
    task_lines.append("\n💡 <i>Cuối tuần được để trống làm Buffer Day để dự phòng dời lịch khi cần.</i>")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 Đồng bộ Google Tasks & Calendar", callback_data="approve_sprint"),
            InlineKeyboardButton(text="❌ Hủy bỏ", callback_data="cancel_setup")
        ]
    ])
    
    await wait_msg.delete()
    await query.message.answer("\n".join(task_lines), reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(GoalSetupState.waiting_sprint_approval)
    await query.answer()


# --- 4. CHỐT SPRINT & ĐẨY LÊN GOOGLE ---
@router.callback_query(GoalSetupState.waiting_sprint_approval, F.data == "approve_sprint")
async def handle_approve_sprint(query: CallbackQuery, state: FSMContext):
    await query.message.edit_reply_markup(reply_markup=None)
    wait_msg = await query.message.answer("📡 Đang đồng bộ công việc lên Google Workspace...")

    data = await state.get_data()
    sprint_tasks = data["sprint_schedule"]["tasks"]
    tasklist_id = data["tasklist_id"]
    goal_id = data["goal_id"]

    try:
        # 1. Gọi Batch API đẩy lên Google Tasks & Calendar
        # task_ids = google_service.batch_create_google_tasks(service, tasklist_id, sprint_tasks)
        # event_ids = google_service.batch_create_calendar_events(service, sprint_tasks)
        
        # 2. Lưu vào Database nội bộ
        # await db_service.save_weekly_tasks(goal_id, sprint_tasks, task_ids, event_ids)

        await wait_msg.delete()
        success_text = (
            "🎉 <b>ĐỒNG BỘ THÀNH CÔNG!</b>\n\n"
            "• Đã tạo danh sách công việc trên <b>Google Tasks</b>.\n"
            "• Đã xếp khung giờ trên <b>Google Calendar</b>.\n\n"
            "🤖 Bot sẽ theo dõi tiến độ và kiểm tra task vào <b>21:30 mỗi tối</b>. "
            "Chúc bạn hoàn thành tốt các mục tiêu đề ra!"
        )
        await query.message.answer(success_text, parse_mode="HTML")
        await state.clear()
        
    except Exception as e:
        await wait_msg.edit_text(f"❌ Quá trình đồng bộ thất bại: {e}")
    
    await query.answer()


# --- 5. XỬ LÝ DỜI LỊCH (MISS TASK TỪ DAILY JOB) ---
@router.callback_query(F.data.startswith("reschedule_"))
async def handle_reschedule_task(query: CallbackQuery):
    """
    Xử lý khi Daily Job gửi tin nhắn báo miss task kèm các nút:
    reschedule_tomorrow_<task_id> hoặc reschedule_weekend_<task_id>
    """
    action, mode, task_id = query.data.split("_")
    
    if mode == "tomorrow":
        # google_service.update_task_deadline(..., new_day="tomorrow")
        await query.message.edit_text(f"✅ Đã dời công việc sang ngày mai trên Google Tasks & Calendar!")
    elif mode == "weekend":
        # google_service.update_task_deadline(..., new_day="saturday")
        await query.message.edit_text(f"✅ Đã chuyển công việc vào ngày đệm Thứ Bảy tuần này!")

    await query.answer()


# --- 6. HỦY / THỬ LẠI ---
@router.callback_query(F.data.in_(["retry_goal", "cancel_setup"]))
async def handle_cancel_or_retry(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(GoalSetupState.waiting_for_goal)
    await query.message.edit_text("Đã hủy bỏ thiết lập. Vui lòng nhập lại mục tiêu mới:")
    await query.answer()