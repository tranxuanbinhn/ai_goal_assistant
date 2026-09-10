from pydantic import BaseModel, Field
from typing import List

class MilestoneOverview(BaseModel):
    phase_number:int = Field(description="Số thứ tự giai đoạn, bắt đầu từ 1")
    title:str = Field(description="Tên giai đoạn (VD: 'Nền tảng cú pháp và thuật toán cơ bản')")
    duration_days:int = Field(description="Thời lượng dự kiến cho giai đoạn này (tính theo ngày)")
    key_outcome:str = Field(description="Kết quả đạt được sau khi hoàn thành giai đoạn này")

class RoadmapOverview(BaseModel):
    goal_title: str = Field(description="Tên mục tiêu đã được chuẩn hóa")
    summary: str = Field(description="Tóm tắt 1-2 câu về chiến lược thực hiện")
    total_estimated_days: int = Field(description="Tổng số ngày dự kiến hoàn thành toàn bộ mục tiêu")
    milestones: List[MilestoneOverview] = Field(description="Danh sách các giai đoạn theo thứ tự")   