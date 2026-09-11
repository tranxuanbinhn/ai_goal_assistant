from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime, timezone

class ExecutableTask(BaseModel):
    title: str = Field(description="Tên task theo chuẩn: [Động từ] + [Đối tượng cụ thể] + [Kết quả đầu ra]")
    notes: Optional[str] = Field(default=None, description="Tiêu chuẩn hoàn thành (DoD - Definition of Done), tài liệu hoặc checklist cụ thể")
    start_time: str = Field(
        description="Thời điểm bắt đầu chính xác định dạng ISO-8601 (YYYY-MM-DDTHH:MM:SS)."
    )
    
    # Dùng cho Google Calendar API (Có đầy đủ ngày, giờ, phút, timezone)
    calendar_start: datetime = Field(description="Thời điểm bắt đầu trên Google Calendar")
    calendar_end: datetime = Field(description="Thời điểm kết thúc trên Google Calendar")
    @computed_field
    @property
    def google_task_due(self) -> str:
        return f"{self.calendar_start.strftime('%Y-%m-%d')}T00:00:00.000Z"
class PhaseTaskSchedule(BaseModel):
    phase_number: int = Field(description="Giai đoạn tương ứng trong roadmap")
    tasks: List[ExecutableTask] = Field(description="Danh sách công việc cụ thể của giai đoạn này")