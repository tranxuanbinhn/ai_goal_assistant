from sqlalchemy.orm import Session
from sqlalchemy import text

from src.core.models.RoadMap import PhaseOverview, RoadmapOverview
from src.core.models.Task import ExecutableTask, PhaseTaskSchedule
from sqlalchemy.ext.asyncio import AsyncSession

async def get_all_roadmaps(db_session:Session):
    query = text("SELECT * FROM road_map")
    return await db_session.execute(query).mappings().all()

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.models.RoadMap import RoadmapOverview

async def save_roadmaps(
    db_session: AsyncSession, 
    roadmap: RoadmapOverview, 
    google_tasklist_id: str,
    user_id: int
) -> int:
    # 1. Tùy chọn: Đặt các roadmap cũ của user này thành không còn active (để tránh xung đột)
    await db_session.execute(
        text("UPDATE road_map SET is_active = FALSE WHERE user_id = :user_id"),
        {"user_id": user_id}
    )

    # 2. Thêm roadmap mới kèm user_id và is_active = TRUE
    query = text("""
        INSERT INTO road_map (
            user_id,
            goal_title,
            google_tasklist_id,
            summary,
            total_estimated_days,
            is_active,
            created_at
        )
        VALUES (
            :user_id,
            :goal_title,
            :google_tasklist_id,
            :summary,
            :total_estimated_days,
            TRUE,
            CURRENT_TIMESTAMP
        )
        RETURNING id
    """)

    result = await db_session.execute(
        query,
        {
            "user_id": user_id,
            "goal_title": roadmap.goal_title,
            "google_tasklist_id": google_tasklist_id,
            "summary": roadmap.summary,
            "total_estimated_days": roadmap.total_estimated_days,
        }
    )
    road_map_id = result.scalar()
    
    await db_session.commit()
    
    return road_map_id
async def get_phase_overview_of_road_map(db_session:AsyncSession, road_map_id:int):
    query = text("""
    SELECT * FROM phase_overview WHERE road_map_id = :road_map_id
    """)
    return await db_session.execute(query, {"road_map_id":road_map_id}).mappings().all()
    
async def save_phase_overview_of_road_map(db_session:AsyncSession, road_map_id:int, phase_overview:PhaseOverview):
    query = text("""
    INSERT INTO phase_overview(
    phase_number, phase_title,phase_description, duration_days,key_outcome,road_map_id,created_at)
    VALUES (:phase_number, :phase_title,:phase_description, :duration_days,:key_outcome,:road_map_id, CURRENT_TIMESTAMP)
    """)
    await db_session.execute(query, {"phase_number":phase_overview.phase_number, "phase_title":phase_overview.phase_title,"phase_description":phase_overview.phase_description, "duration_days":phase_overview.duration_days,"key_outcome":phase_overview.key_outcome,"road_map_id":road_map_id})
    await db_session.commit()
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_phase(db_session: AsyncSession, road_map_id: int):
   
    query = text("""
        SELECT id, phase_number, phase_title, phase_description, duration_days, key_outcome, status
        FROM phase_overview
        WHERE road_map_id = :road_map_id AND status = 'IN_PROGRESS'
        ORDER BY phase_number ASC
        LIMIT 1
    """)
    result = await db_session.execute(query, {"road_map_id": road_map_id})
    current_phase = result.mappings().first()

    # Nếu chưa có phase nào IN_PROGRESS, kích hoạt Phase đầu tiên
    if not current_phase:
        init_query = text("""
            UPDATE phase_overview
            SET status = 'IN_PROGRESS'
            WHERE id = (
                SELECT id FROM phase_overview
                WHERE road_map_id = :road_map_id
                ORDER BY phase_number ASC
                LIMIT 1
            )
            RETURNING id, phase_number, phase_title, phase_description, duration_days, key_outcome, status
        """)
        init_result = await db_session.execute(init_query, {"road_map_id": road_map_id})
        await db_session.commit()
        current_phase = init_result.mappings().first()

    return current_phase
async def save_week_number_phase_overview(
    db_session: AsyncSession, 
    road_map_id: int, 
    phase_overview: PhaseOverview, 
    week_number: int
) -> int:
    query = text("""
        UPDATE phase_overview
        SET week_number = :week_number
        WHERE road_map_id = :road_map_id AND phase_number = :phase_number
        RETURNING week_number
    """)
    
    result = await db_session.execute(
        query, 
        {
            "week_number": week_number,
            "road_map_id": road_map_id,
            "phase_number": phase_overview.phase_number  # Lấy từ thuộc tính của object
        }
    )
    
    # Commit để lưu thay đổi vào Database
    await db_session.commit()
    
    updated_week = result.scalar()
    return updated_week or week_number
async def get_next_week_number(
    db_session: AsyncSession, 
    road_map_id: int, 
    phase_number: int
) -> int:
    query = text("""
        SELECT COALESCE(MAX(pt.week_number), 0) + 1 AS next_week
        FROM phase_task pt
        JOIN phase_overview po ON pt.phase_overview_id = po.id
        WHERE po.road_map_id = :road_map_id AND pt.phase_number = :phase_number
    """)
    result = await db_session.execute(
        query, 
        {"road_map_id": road_map_id, "phase_number": phase_number}
    )
    next_week = result.scalar()
    return next_week or 1
async def get_phase_task_of_phase_overview(db_session:AsyncSession, phase_overview_id:int):
    query = text("""
    SELECT * FROM phase_task WHERE phase_overview_id = :phase_overview_id
    """)
    return await db_session.execute(query, {"phase_overview_id":phase_overview_id}).mappings().all()

async def save_phase_task_of_phase_overview(db_session:AsyncSession, phase_overview_id:int, phase_task:PhaseTaskSchedule):
    query = text("""
    INSERT INTO phase_task(
    phase_number, week_number,week_start_date, phase_overview_id,created_at)
    VALUES (:phase_number, :week_number,:week_start_date, :phase_overview_id, CURRENT_TIMESTAMP)
    RETURNING id
    """)
    result=await db_session.execute(query, {"phase_number":phase_task.phase_number, "week_number":phase_task.week_number,"week_start_date":phase_task.week_start_date, "phase_overview_id":phase_overview_id})
    task_id = result.scalar()
    await db_session.commit()
    return task_id

async def get_task_of_phase_task(db_session:AsyncSession, phase_task_id:int):
    query = text("""
    SELECT * FROM task WHERE phase_task_id = :phase_task_id
    """)
    return await db_session.execute(query, {"phase_task_id":phase_task_id}).mappings().all()

async def save_task_of_phase_task(db_session:AsyncSession, phase_task_id:int, executable_Task:ExecutableTask):
    query = text("""
    INSERT INTO task(
    title, notes,calendar_start, calendar_end,phase_task_id,created_at)
    VALUES (:title, :notes, :calendar_start, :calendar_end, :phase_task_id, CURRENT_TIMESTAMP)
    """)
    await db_session.execute(query, {"title":executable_Task.title, "notes":executable_Task.notes,"calendar_start":executable_Task.calendar_start, "calendar_end":executable_Task.calendar_end,"phase_task_id":phase_task_id})
    await db_session.commit()

async def get_list_task_id_from_road_map(db_session:AsyncSession, road_map_id:str):
    query = text(
        """
        SELECT google_tasklist_id FROM road_map
        WHERE id = :road_map_id
        """)
    return await db_session.execute(query, {"road_map_id":road_map_id}).mappings().first()

async def update_list_task_id_for_road_map(db_session:AsyncSession, road_map_id:str, google_tasklist_id:str):
    query = text(
        """
        UPDATE road_map
        SET google_tasklist_id = :google_tasklist_id
        WHERE id = :road_map_id
        RETURNING *
        """)
    result = await db_session.execute(query, {"road_map_id":road_map_id, "google_tasklist_id":google_tasklist_id})
    await db_session.commit()
    return result.mappings().first()
    
async def mark_phase_task_completed(db_session: AsyncSession, phase_task_id: int):
    query = text("""
        UPDATE phase_task
        SET is_completed = TRUE
        WHERE id = :phase_task_id
    """)
    await db_session.execute(query, {"phase_task_id": phase_task_id})
    await db_session.commit()

async def check_can_create_next_week(db_session: AsyncSession, road_map_id: int):
  
    query = text("""
        SELECT pt.id, pt.phase_number, pt.week_number, pt.is_completed
        FROM phase_task pt
        JOIN phase_overview po ON pt.phase_overview_id = po.id
        WHERE po.road_map_id = :road_map_id
        ORDER BY pt.id DESC
        LIMIT 1
    """)
    result = await db_session.execute(query, {"road_map_id": road_map_id})
    latest = result.mappings().first()

    # Trường hợp 1: Chưa từng tạo tuần nào -> Cho phép tạo Tuần 1
    if not latest:
        return True, None, "Chưa có tuần nào, có thể tạo mới."

    # Trường hợp 2: Tuần trước đã bấm hoàn thành -> Cho phép tạo tuần kế tiếp
    if latest["is_completed"]:
        return True, latest["id"], "Tuần cũ đã xong, có thể tạo tuần mới."

    # Trường hợp 3: Tuần cũ chưa bấm hoàn thành -> Chặn lại
    return False, latest["id"], f"Bạn chưa hoàn thành Phase {latest['phase_number']} - Tuần {latest['week_number']}!"