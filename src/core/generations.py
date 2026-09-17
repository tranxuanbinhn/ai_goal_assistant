from google.genai import types
from google import genai
from dotenv import load_dotenv
from src.core.db.handlegoal import get_all_roadmaps, get_phase_overview_of_road_map, get_phase_task_of_phase_overview, get_task_of_phase_task, save_phase_overview_of_road_map, save_phase_task_of_phase_overview, save_roadmaps, save_task_of_phase_task
from src.core.models.Task import PhaseTaskSchedule
from src.core.models.RoadMap import RoadmapOverview
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import TypeAdapter
from src.core.logging.logger_config import setup_logger
from src.core.db.database import init_db, SessionLocal
load_dotenv()
logger = setup_logger()
session = SessionLocal()
API_KEY =os.getenv("GEMINI_API_KEY")
init_db = init_db()
class Generation():
    def __init__(self, api_key:str | None):
        self.client = genai.Client(api_key=api_key)
        
    def generateRoadmap(self, promt:str)->RoadmapOverview:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RoadmapOverview
        )
        chat = self.client.chats.create(
            model="gemini-3.5-flash",
            config=config,
        )
        response = chat.send_message(promt)
        return RoadmapOverview.model_validate_json(response.text)
    def generateTask(self,roadMapOvervieww:RoadmapOverview, target_phase_number:int,week_number:int = 1, preferred_start_hour: int = 19 ,daily_hours_limit: float = 2.0,timezone_str: str = "Asia/Ho_Chi_Minh" )-> PhaseTaskSchedule:
        current_phase = next (
           (p for p in roadMapOvervieww.phase_task if p.phase_number == target_phase_number), None 
        )
        if not current_phase:
            logger.debug("Khong the tim ra phase")
            raise "Khong tim ra phase"
        now = datetime.now(ZoneInfo(timezone_str))
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S (%A)")
        tz_offset = now.strftime("%z")
        formatted_tz_offset = f"{tz_offset[:3]}:{tz_offset[3:]}"

        roadmap_summary = {
            "goal_title":roadMapOvervieww.goal_title,
            "current_phase":f"{current_phase.phase_number}: {current_phase.phase_title}",
            "phase_duration_days":current_phase.duration_days,
            "phase_key_outcome":current_phase.key_outcome
        }

        prompt = f"""
        Bạn là một chuyên gia quản trị dự án Agile và tối ưu năng suất cá nhân (Productivity & Agile Coach).
        Nhiệm vụ của bạn là nhận thông tin của MỘT GIAI ĐOẠN CỤ THỂ (Phase) trong lộ trình tổng thể và bẻ nhỏ giai đoạn này thành danh sách các đầu việc thực thi (Executable Tasks) theo từng ngày.

        [DỮ LIỆU ĐẦU VÀO CỦA PHASE HIỆN TẠI]
        - Mục tiêu tổng quát: {roadmap_summary['goal_title']}
        - Giai đoạn thực hiện: Phase {roadmap_summary['current_phase']}
        - Kết quả đầu ra bắt buộc (Key Outcome): {roadmap_summary['phase_key_outcome']}

        [RÀNG BUỘC THỜI GIAN]
        - Mốc thời gian tham chiếu hiện tại: {current_time_str}
        - Múi giờ: {timezone_str} (Offset: {formatted_tz_offset})
        - Quỹ thời gian tối đa: {daily_hours_limit} giờ/ngày.
        - Khung giờ ưu tiên bắt đầu: Từ {preferred_start_hour}:00 hàng ngày.
        - Giới hạn lập lịch: CHỈ xếp lịch cho 7 ngày tới kể từ {current_time_str}.
        [NGUYÊN TẮC THIẾT KẾ TASK THỰC THI]
        1. NGUYÊN TẮC HÀNH ĐỘNG VÀ ĐẦU RA:
        - Tên công việc (title) phải bắt đầu bằng động từ hành động cụ thể và gắn với kết quả hữu hình (Ví dụ: "Viết module xác thực người dùng", "Giải 5 bài tập Array LeetCode"). Tránh các task chung chung như "Học lý thuyết", "Tìm hiểu tài liệu".
        - Mỗi task phải có thời lượng từ 30 đến 90 phút (tối đa không quá 120 phút).
        - Phần mô tả (notes) phải chứa: (1) Mục tiêu ngắn, (2) Tài liệu/đường dẫn hoặc tiêu chí hoàn thành, (3) Khung giờ đề xuất.

        2. NGUYÊN TẮC ĐỆM THỜI GIAN (BUFFER DAYS - BẮT BUỘC):
        - Trong chu kỳ 7 ngày, CHỈ xếp việc vào tối đa 5 ngày làm việc.
        - BẮT BUỘC để trống 1 - 2 ngày (ưu tiên cuối tuần hoặc ngày thứ 6/thứ 7) làm "Catch-up/Buffer Day". KHÔNG gán bất kỳ task mới nào vào những ngày này để dự phòng cho việc xử lý task trễ hoặc ôn tập.

        3. RÀNG BUỘC ĐỒNG BỘ GOOGLE TASKS & CALENDAR:
        - Tất cả mốc thời gian PHẢI bắt đầu từ tương lai (sau {current_time_str}).
        - Tổng estimated_minutes của các task trong một ngày <= {daily_hours_limit} * 60 phút.
        - KHÔNG xếp lịch vào khung giờ ngủ (22:30 - 06:30).
        - Khoảng cách giữa `calendar_start` và `calendar_end` phải khớp chính xác với `estimated_minutes`.
         """
        config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PhaseTaskSchedule,
                    temperature=0.2
                )
        response = self.client.models.generate_content(
            model="gemini-3.5-flash",
            contents= prompt,
            config=config
            
        )
        
        return PhaseTaskSchedule.model_validate_json(response.text)

if __name__=="__main__":
    #gen = Generation(api_key=API_KEY)
    #promt = "Hãy tạo một lộ trình tổng quan (Roadmap Overview) học lập trình Backend với Python cho người mới bắt đầu từ con số 0 trong vòng 6 tháng"
    #rs = gen.generateRoadmap(promt=promt)
    ##print(rs)
    #rs_task = gen.generateTask(roadMapOvervieww=rs,target_phase_number=1)
    #print(f"rs_task {rs_task}")
    
    #save_roadmaps(session,rs)
    print("***-***")
    #print(get_all_roadmaps(session))

    #list_phase_task = rs.phase_task
    #for phase_task in list_phase_task:
    #    save_phase_overview_of_road_map(session, 1, phase_task)
    #save_phase_overview_of_road_map(session, 1, )
    #print("In ra man hinh phase overview")
    #print(get_phase_overview_of_road_map(session, 1))
    
    #print("Phase task")
    #print(get_phase_task_of_phase_overview(db_session=session, phase_overview_id=1))
    #save_phase_task_of_phase_overview(db_session=session,phase_overview_id=1, phase_task=rs_task)
    
    #for task in rs_task.tasks:
    #    save_task_of_phase_task(db_session=session, phase_task_id=1, executable_Task=task)
    print("get task")    
    print(get_task_of_phase_task(db_session=session, phase_task_id=1))