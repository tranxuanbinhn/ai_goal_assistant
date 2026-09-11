from pydantic import BaseModel, Field
from typing import List
from src.core.models.Task import PhaseTaskSchedule


class RoadmapOverview(BaseModel):
    goal_title: str = Field(description="Tên mục tiêu đã được chuẩn hóa")
    summary: str = Field(description="Tóm tắt 1-2 câu về chiến lược thực hiện")
    total_estimated_days: int = Field(description="Tổng số ngày dự kiến hoàn thành toàn bộ mục tiêu")
    phase_task: List[PhaseTaskSchedule] = Field(description="Danh sách các giai đoạn theo thứ tự")   