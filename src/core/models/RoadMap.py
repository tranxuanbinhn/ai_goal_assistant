from pydantic import BaseModel, Field
from typing import List
from src.core.models.Task import PhaseTaskSchedule

class PhaseOverview(BaseModel):
    phase_number: int = Field(description="Số thứ tự của giai đoạn, bắt đầu từ 1 (ví dụ: 1, 2, 3)")
    phase_title: str = Field(description="Tên ngắn gọn của giai đoạn (VD: 'Nền tảng TypeScript & Kiến trúc Test')")
    phase_description: str = Field(description="Mô tả trọng tâm chiến lược của giai đoạn này")
    duration_days: int = Field(description="Thời lượng ước tính của phase (VD: 14, 21, 28 ngày)")
    key_outcome: str = Field(
        description=(
            "Kết quả cốt lõi, hữu hình và đo lường được cần đạt được khi kết thúc giai đoạn này. "
            "Phải bao gồm sản phẩm cụ thể (artifact) hoặc chỉ số kiểm chứng (metrics). "
            "Ví dụ: 'Hoàn thành test suite 10 ca kiểm thử cho trang Checkout'. "
            "Tuyệt đối không dùng các câu chung chung như 'Hiểu kiến thức cơ bản'."
        )
    )

class RoadmapOverview(BaseModel):
    goal_title: str = Field(description="Tên mục tiêu đã được chuẩn hóa")
    summary: str = Field(description="Tóm tắt 1-2 câu về chiến lược thực hiện")
    total_estimated_days: int = Field(description="Tổng số ngày dự kiến hoàn thành toàn bộ mục tiêu")
    phase_task: List[PhaseOverview] = Field(description="Danh sách các giai đoạn theo thứ tự")   

