from google.genai import types
from google import genai
from dotenv import load_dotenv
from src.core.models.Task import PhaseTaskSchedule
from src.core.models.RoadMap import RoadmapOverview
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import TypeAdapter
load_dotenv()
API_KEY =os.getenv("GEMINI_API_KEY")
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
    def generatePhaseTask(self,roadMapOvervieww:RoadmapOverview, preferred_start_hour: int = 19 ,daily_hours_limit: float = 2.0,timezone_str: str = "Asia/Ho_Chi_Minh")-> list[PhaseTaskSchedule]:
        now = datetime.now(ZoneInfo(timezone_str))
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S (%A)")
        road_map_json = roadMapOvervieww.model_dump_json(indent=2)

        prompt = f"""
        Bạn là một chuyên gia quản lý dự án và tối ưu hóa năng suất cá nhân (Productivity & Agile Coach).
        Nhiệm vụ của bạn là bẻ nhỏ một mục tiêu tổng thể thành một lộ trình thực thi chi tiết, khả thi và gán mốc thời gian thực tế.
        Dữ liệu road map hiện tại {road_map_json}
        [THÔNG TIN BỐI CẢNH]
        - Thời điểm hiện tại: {current_time_str}
        - Múi giờ: {timezone_str}
        - Quỹ thời gian tối đa mỗi ngày của người dùng: {daily_hours_limit} giờ/ngày.
        - Khung giờ học tập/làm việc ưu tiên: Bắt đầu từ khoảng {preferred_start_hour}:00 hàng ngày.
        [NGUYÊN TẮC CHIA TASK & ƯỚC LƯỢNG THỜI GIAN]
        1. QUY TẮC PHÂN RÃ:
        - Chia việc theo luồng logic tuần tự: Chuẩn bị -> Thực thi -> Đánh giá/Kiểm thử.
        - Mỗi task phải là một hành động cụ thể, bắt đầu bằng động từ (e.g., "Đọc chương 1", "Viết script kiểm thử", "Tạo file config").
        - Không tạo task quá lớn (> 120 phút). Nếu việc cần nhiều thời gian, hãy bẻ thành Part 1, Part 2.
        
        2. QUY TẮC LẬP LỊCH & ĐỊNH DANH THỜI GIAN:
        - Tất cả mốc thời gian (start_time, due_time) PHẢI bắt đầu từ tương lai (sau thời điểm hiện tại).
        - Tổng thời lượng các task trong một ngày KHÔNG ĐƯỢC vượt quá {daily_hours_limit} giờ.
        - Tránh xếp lịch vào khung giờ đêm (23:00 - 06:00) trừ khi được yêu cầu.
        - Khoảng cách giữa start_time và due_time phải khớp với estimated_minutes.
        - Định dạng bắt buộc: YYYY-MM-DDTHH:MM:SS (ví dụ: 2026-09-10T19:30:00).

        
        """
        config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[PhaseTaskSchedule],
                    temperature=0.2
                )
        response = self.client.models.generate_content(
            model="gemini-3.5-flash",
            contents= prompt,
            config=config
            
        )
        adapter = TypeAdapter(list[PhaseTaskSchedule])
        return adapter.validate_json(response.text)

if __name__=="__main__":
    gen = Generation(api_key=API_KEY)
    promt = "Hãy tạo một lộ trình tổng quan (Roadmap Overview) học lập trình Backend với Python cho người mới bắt đầu từ con số 0 trong vòng 6 tháng"
    rs = gen.generateRoadmap(promt=promt)
    print(rs)
    listtask = gen.generatePhaseTask(roadMapOvervieww=rs)
    print(f"listtask: {listtask}")