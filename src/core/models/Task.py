from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime, timezone, date

class ExecutableTask(BaseModel):
    title: str = Field(description="Tên task theo chuẩn: [Động từ] + [Đối tượng cụ thể] + [Kết quả đầu ra]")
    notes: Optional[str] = Field(default=None, description="Tiêu chuẩn hoàn thành (DoD - Definition of Done), tài liệu hoặc checklist cụ thể")
    
    
    # Dùng cho Google Calendar API (Có đầy đủ ngày, giờ, phút, timezone)
    calendar_start: datetime = Field(description="Thời điểm bắt đầu trên Google Calendar")
    calendar_end: datetime = Field(description="Thời điểm kết thúc trên Google Calendar")
    @computed_field
    @property
    def google_task_due(self) -> str:
        local_date = self.calendar_end.date()
        return f"{local_date.isoformat()}T00:00:00.000Z"
class PhaseTaskSchedule(BaseModel):
    phase_number: int = Field(description="Giai đoạn tương ứng trong roadmap")
    week_number: int = Field(description="Số thứ tự tuần đang thực hiện trong giai đoạn này (ví dụ: Tuần 1)")
    key_outcome:str = Field(description="Kết quả cốt lõi, hữu hình và đo lường được cần đạt được khi kết thúc giai đoạn này. "
            "Phải bao gồm sản phẩm cụ thể (artifact) hoặc chỉ số kiểm chứng (metrics). "
            "Ví dụ: 'Hoàn thành ứng dụng To-Do List chạy bằng Vanilla JS' hoặc "
            "'Đạt tối thiểu 80% điểm số trong bài mock-test 50 câu về SQL Joins'. "
            "Tuyệt đối không dùng các câu chung chung như 'Hiểu kiến thức cơ bản'.")
    phase_description: str = Field(description="Mô tả tổng quan về phase này trong roadmap")
    week_start_date: date = Field(description="Ngày Thứ Hai bắt đầu tuần này (YYYY-MM-DD)")
    tasks: List[ExecutableTask] = Field(description="Danh sách 4-6 công việc cụ thể phân bổ từ Thứ Hai đến Thứ Sáu (chừa cuối tuần làm ngày đệm)")