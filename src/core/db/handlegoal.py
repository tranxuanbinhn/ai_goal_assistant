from sqlalchemy.orm import Session
from sqlalchemy import text

from src.core.models.RoadMap import PhaseOverview, RoadmapOverview
from src.core.models.Task import ExecutableTask, PhaseTaskSchedule
from sqlalchemy.ext.asyncio import AsyncSession

async def get_all_roadmaps(db_session:Session):
    query = text("SELECT * FROM road_map")
    return await db_session.execute(query).mappings().all()

async def save_roadmaps(db_session:AsyncSession, roadmap:RoadmapOverview, google_tasklist_id:str):
    query = text("""
    INSERT INTO road_map(
    goal_title,google_tasklist_id, summary,total_estimated_days, created_at)
    VALUES (:goal_title, :summary, :total_estimated_days, CURRENT_TIMESTAMP)
    """)
    await db_session.execute(query, {"goal_title":roadmap.goal_title,"google_tasklist_id":google_tasklist_id,"summary":roadmap.summary, "total_estimated_days":roadmap.total_estimated_days})
    await db_session.commit()

async def get_phase_overview_of_road_map(db_session:Session, road_map_id:int):
    query = text("""
    SELECT * FROM phase_overview WHERE road_map_id = :road_map_id
    """)
    return await db_session.execute(query, {"road_map_id":road_map_id}).mappings().all()
    
async def save_phase_overview_of_road_map(db_session:Session, road_map_id:int, phase_overview:PhaseOverview):
    query = text("""
    INSERT INTO phase_overview(
    phase_number, phase_title,phase_description, duration_days,key_outcome,road_map_id,created_at)
    VALUES (:phase_number, :phase_title,:phase_description, :duration_days,:key_outcome,:road_map_id, CURRENT_TIMESTAMP)
    """)
    await db_session.execute(query, {"phase_number":phase_overview.phase_number, "phase_title":phase_overview.phase_title,"phase_description":phase_overview.phase_description, "duration_days":phase_overview.duration_days,"key_outcome":phase_overview.key_outcome,"road_map_id":road_map_id})
    await db_session.commit()

async def get_phase_task_of_phase_overview(db_session:Session, phase_overview_id:int):
    query = text("""
    SELECT * FROM phase_task WHERE phase_overview_id = :phase_overview_id
    """)
    return await db_session.execute(query, {"phase_overview_id":phase_overview_id}).mappings().all()

async def save_phase_task_of_phase_overview(db_session:Session, phase_overview_id:int, phase_task:PhaseTaskSchedule):
    query = text("""
    INSERT INTO phase_task(
    phase_number, week_number,week_start_date, phase_overview_id,created_at)
    VALUES (:phase_number, :week_number,:week_start_date, :phase_overview_id, CURRENT_TIMESTAMP)
    """)
    await db_session.execute(query, {"phase_number":phase_task.phase_number, "week_number":phase_task.week_number,"week_start_date":phase_task.week_start_date, "phase_overview_id":phase_overview_id})
    await db_session.commit()

async def get_task_of_phase_task(db_session:Session, phase_task_id:int):
    query = text("""
    SELECT * FROM task WHERE phase_task_id = :phase_task_id
    """)
    return await db_session.execute(query, {"phase_task_id":phase_task_id}).mappings().all()

async def save_task_of_phase_task(db_session:Session, phase_task_id:int, executable_Task:ExecutableTask):
    query = text("""
    INSERT INTO task(
    title, notes,calendar_start, calendar_end,phase_task_id,created_at)
    VALUES (:title, :notes, :calendar_start, :calendar_end, :phase_task_id, CURRENT_TIMESTAMP)
    """)
    await db_session.execute(query, {"title":executable_Task.title, "notes":executable_Task.notes,"calendar_start":executable_Task.calendar_start, "calendar_end":executable_Task.calendar_end,"phase_task_id":phase_task_id})
    await db_session.commit()

async def get_list_task_id_from_road_map(db_session:Session, road_map_id:str):
    query = text(
        """
        SELECT google_tasklist_id FROM road_map
        WHERE id = :road_map_id
        """)
    return await db_session.execute(query, {"road_map_id":road_map_id}).mappings().first()

async def update_list_task_id_for_road_map(db_session:Session, road_map_id:str, google_tasklist_id:str):
    query = text(
        """
        UPDATE road_map
        SET google_tasklist_id = :google_tasklist_id
        WHERE id = :road_map_id
        RETURNING *
        """)
    result = await db_session.execute(query, {"road_map_id":road_map_id, "google_tasklist_id":google_tasklist_id})
    await db_session.commit()
    return await result.mappings().first()
    