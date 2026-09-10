from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class ExecutableTask(BaseModel):
    title: str = Field(description="Tên công việc (VD: 'Luyện tập 5 bài LeetCode')")
    notes: Optional[str] = Field(default=None, description="Chi tiết công việc hoặc tài liệu hướng dẫn")
    
    # Dùng cho Google Tasks API (Chỉ lấy ngày: YYYY-MM-DD)
    due_date: date = Field(description="Hạn chót tính theo ngày cho Google Tasks")
    
    # Dùng cho Google Calendar API (Có đầy đủ ngày, giờ, phút, timezone)
    calendar_start: datetime = Field(description="Thời điểm bắt đầu trên Google Calendar")
    calendar_end: datetime = Field(description="Thời điểm kết thúc trên Google Calendar")

class PhaseTaskSchedule(BaseModel):
    phase_number: int = Field(description="Giai đoạn tương ứng trong roadmap")
    tasks: List[ExecutableTask] = Field(description="Danh sách công việc cụ thể của giai đoạn này")