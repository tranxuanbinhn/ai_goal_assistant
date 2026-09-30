from aiogram.fsm.state import State, StatesGroup

class GoalSetupState(StatesGroup):
    waiting_for_goal = State()       # Chờ người dùng nhập mục tiêu
    waiting_roadmap_approval = State() # Đang hiển thị Roadmap, chờ bấm duyệt
    waiting_sprint_approval = State()  # Đang hiển thị task 7 ngày, chờ bấm chốt