from sqlalchemy.orm import Session
from sqlalchemy import text

from core.models.RoadMap import PhaseOverview, RoadmapOverview
from core.models.Task import ExecutableTask, PhaseTaskSchedule


def get_all_roadmaps(db_session:Session):
    query = text("SELECT * FROM road_map")
    return db_session.execute(query).mappings().all()

def save_roadmaps(db_session:Session, roadmap:RoadmapOverview):
    query = text("""
    INSERT INTO road_map(
    goal_title, summary,total_estimated_days, created_at)
    VALUES (:goal_title, :summary, :total_estimated_days, CURRENT_TIMESTAMP)
    """)
    db_session.execute(query, {"goal_title":roadmap.goal_title,"summary":roadmap.summary, "total_estimated_days":roadmap.total_estimated_days})
    db_session.commit()

def get_phase_overview_of_road_map(db_session:Session, road_map_id:int):
    query = """
    SELECT * FROM phase_overview WHERE road_map_id = :road_map_id
    """
    return db_session.execute(query, {"road_map_id":road_map_id}).mappings().all()
    
def save_phase_overview_of_road_map(db_session:Session, road_map_id:int, phase_overview:PhaseOverview):
    query = text("""
    INSERT INTO phase_overview(
    phase_number, phase_title,phase_description, duration_days,key_outcome,road_map_id,created_at)
    VALUES (:phase_number, :phase_title,:phase_description, :duration_days,:key_outcome,:road_map_id, CURRENT_TIMESTAMP)
    """)
    db_session.execute(query, {"phase_number":phase_overview.phase_number, "phase_title":phase_overview.phase_title,"phase_description":phase_overview.phase_description, "duration_days":phase_overview.duration_days,"key_outcome":phase_overview.key_outcome,"road_map_id":road_map_id})
    db_session.commit()

def get_phase_task_of_phase_overview(db_session:Session, phase_overview_id:int):
    query = """
    SELECT * FROM phase_task WHERE phase_overview_id = :phase_overview_id
    """
    return db_session.execute(query, {"phase_overview_id":phase_overview_id}).mappings().all()

def save_phase_task_of_phase_overview(db_session:Session, phase_overview_id:int, phase_task:PhaseTaskSchedule):
    query = text("""
    INSERT INTO phase_task(
    phase_number, week_number,week_start_date, phase_overview_id,created_at)
    VALUES (:phase_number, :week_number,:week_start_date, :phase_overview_id, CURRENT_TIMESTAMP)
    """)
    db_session.execute(query, {"phase_number":phase_task.phase_number, "week_number":phase_task.week_number,"week_start_date":phase_task.week_start_date, "phase_overview_id":phase_overview_id})
    db_session.commit()

def get_task_of_phase_task(db_session:Session, phase_task_id:int):
    query = """
    SELECT * FROM task WHERE phase_task_id = :phase_task_id
    """
    return db_session.execute(query, {"phase_task_id":phase_task_id}).mappings().all()

def save_task_of_phase_task(db_session:Session, phase_task_id:int, executable_Task:ExecutableTask):
    query = text("""
    INSERT INTO task(
    title, notes,calendar_start, calendar_end,phase_task_id,created_at)
    VALUES (:title, :notes, :calendar_start, :calendar_end, :phase_task_id, CURRENT_TIMESTAMP)
    """)
    db_session.execute(query, {"title":executable_Task.title, "notes":executable_Task.notes,"calendar_start":executable_Task.calendar_start, "calendar_end":executable_Task.calendar_end,"phase_task_id":phase_task_id})
    db_session.commit()