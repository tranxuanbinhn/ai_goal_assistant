# AI Goal Assistant

**AI Goal Assistant** là dự án trợ lý cá nhân ứng dụng trí tuệ nhân tạo (AI), được xây dựng bằng Python. Repository tích hợp Google Gemini, Telegram Bot và PostgreSQL cùng các thư viện hỗ trợ quản lý dữ liệu, cấu hình và xác thực.

🔗 **Repository:** [tranxuanbinhn/ai_goal_assistant](https://github.com/tranxuanbinhn/ai_goal_assistant)

## 📋 Mục lục

- [Giới thiệu](#-giới-thiệu)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu hình môi trường](#-cấu-hình-môi-trường)
- [Chạy ứng dụng](#-chạy-ứng-dụng)
- [Kiểm thử và xử lý lỗi](#-kiểm-thử-và-xử-lý-lỗi)
- [Đóng góp](#-đóng-góp)
- [Giấy phép](#-giấy-phép)

## 🎯 Giới thiệu

AI Goal Assistant hướng đến việc xây dựng một trợ lý AI hỗ trợ người dùng trong các tác vụ liên quan đến mục tiêu cá nhân.
AI Goal Assistant giúp tạo mục tiêu, chia mục tiêu thành từng giai đoạn, rồi tạo google task cho từng tuần trong các giai đoạn


## 🛠️ Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| Python | Ngôn ngữ lập trình chính |
| Google Gen AI SDK | Tích hợp mô hình AI của Google |
| aiogram | Xây dựng Telegram Bot |
| PostgreSQL | Hệ quản trị cơ sở dữ liệu |
| SQLAlchemy | ORM và quản lý truy cập dữ liệu |
| asyncpg | Kết nối PostgreSQL bất đồng bộ |
| psycopg2-binary | Bộ điều hợp PostgreSQL cho Python |
| Pydantic | Xác thực và quản lý dữ liệu |
| python-dotenv | Đọc cấu hình từ biến môi trường |
| Google API Client | Tích hợp các dịch vụ Google |
| Google Auth | Xác thực với các dịch vụ Google |
| tzdata | Hỗ trợ dữ liệu múi giờ |

## 📁 Cấu trúc dự án

Cấu trúc cấp gốc đã xác định được:

```text
## 📁 Cấu trúc dự án

```text
ai_goal_assistant/
├── logs/                         # Thư mục lưu log ứng dụng
├── src/
│   ├── core/
│   │   ├── db/
│   │   │   ├── database.py       # Thành phần kết nối và quản lý database
│   │   │   └── handlegoal.py     # Xử lý nghiệp vụ liên quan đến mục tiêu
│   │   ├── logging/
│   │   │   └── logger_config.py  # Cấu hình logging
│   │   ├── models/
│   │   │   ├── handle.py         # Xử lý nghiệp vụ của model
│   │   │   ├── RoadMap.py        # Thành phần liên quan đến lộ trình
│   │   │   └── Task.py           # Thành phần liên quan đến nhiệm vụ
│   │   └── generations.py        # Thành phần tạo nội dung bằng AI
│   ├── integrations/
│   │   └── bot_handlers.py       # Xử lý tương tác với bot
│   ├── main.py                   # Tệp khởi chạy ứng dụng (cần xác minh)
│   ├── service.py                # Lớp dịch vụ xử lý nghiệp vụ
│   └── states.py                 # Quản lý trạng thái hội thoại
├── requirements.txt              # Danh sách thư viện phụ thuộc
├── .gitignore                    # Các tệp và thư mục loại trừ khỏi Git
└── README.md                     # Tài liệu dự án
```

### 🧩 Các thành phần chính

- **`core/db/`**: Tổ chức các thành phần liên quan đến cơ sở dữ liệu và xử lý mục tiêu.
- **`core/logging/`**: Cấu hình hệ thống ghi log phục vụ theo dõi và gỡ lỗi.
- **`core/models/`**: Chứa các module liên quan đến 
xử lý model, lộ trình và nhiệm vụ.
- **`core/generations.py`**: Dựa trên tên tệp, có thể là thành phần tạo nội dung hoặc kế hoạch bằng AI; cần kiểm tra mã nguồn để xác nhận.
- **`integrations/bot_handlers.py`**: Thành phần tích hợp và xử lý tương tác với bot.
- **`main.py`**: Có thể là điểm khởi chạy chính của ứng dụng.
- **`service.py`**: Có thể đảm nhiệm việc kết nối các thành phần và điều phối nghiệp vụ.
- **`states.py`**: Có thể định nghĩa trạng thái hội thoại hoặc quy trình xử lý tương tác.

```

## 💻 Yêu cầu hệ thống

Trước khi cài đặt, cần chuẩn bị:

- Python tương thích với các phiên bản thư viện trong dự án.
- Git để tải mã nguồn.
- PostgreSQL nếu ứng dụng sử dụng cơ sở dữ liệu này khi chạy.
- Thông tin xác thực Google AI nếu luồng xử lý AI yêu cầu gọi API.
- Token Telegram Bot nếu ứng dụng sử dụng bot Telegram.

Các dịch vụ và thông tin xác thực cần thiết phụ thuộc vào cấu hình triển khai thực tế.

## 🚀 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/tranxuanbinhn/ai_goal_assistant.git
cd ai_goal_assistant
```

### 2. Tạo môi trường ảo

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Cài đặt dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## ⚙️ Cấu hình môi trường

Tạo tệp `.env` tại thư mục gốc nếu ứng dụng sử dụng biến môi trường để lưu cấu hình.

Ví dụ về các nhóm cấu hình có thể cần:

```dotenv
# Google AI
GEMINI_API_KEY=your_google_ai_api_key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# PostgreSQL
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

**Quan trọng:** Đây là ví dụ minh họa, không phải danh sách biến đã được xác minh từ mã nguồn. Hãy đối chiếu tên biến với phần cấu hình và các module trong `src/` trước khi sử dụng. Không đưa API key, token hoặc mật khẩu thật lên GitHub.

## ▶️ Chạy ứng dụng

Sau khi cài đặt dependencies và hoàn tất cấu hình:

1. Kiểm tra cấu hình môi trường.
2. Đảm bảo các dịch vụ phụ thuộc đã sẵn sàng.
3. Xác định module khởi chạy và lệnh chạy được dự án hỗ trợ.
4. Khởi động ứng dụng theo hướng dẫn tương ứng với entry point thực tế.

Lệnh chạy chính xác chưa được ghi ở đây vì cần xác minh tệp khởi chạy bên trong `src/`.

## 🧪 Kiểm thử và xử lý lỗi

Kiểm tra cú pháp các tệp Python khi cần:

```bash
python -m compileall src
```

Một số vấn đề thường gặp khi thiết lập dự án:

- **Lỗi thiếu thư viện:** Kiểm tra môi trường ảo và cài lại dependencies.
- **Lỗi xác thực Google AI:** Kiểm tra API key, quyền truy cập và cấu hình dịch vụ.
- **Lỗi Telegram Bot:** Kiểm tra token và cấu hình bot.
- **Lỗi kết nối PostgreSQL:** Kiểm tra địa chỉ máy chủ, cổng, thông tin đăng nhập và tên cơ sở dữ liệu.
- **Lỗi biến môi trường:** Đối chiếu tên biến trong `.env` với mã nguồn thực tế.

Các lệnh kiểm thử chức năng cần được bổ sung khi xác định được bộ kiểm thử và cách chạy ứng dụng.

## 🤝 Đóng góp

Mọi đóng góp nhằm cải thiện mã nguồn, tài liệu và chất lượng dự án đều được hoan nghênh.

Quy trình đề xuất:

1. Fork repository.
2. Tạo nhánh mới cho thay đổi.
3. Thực hiện và kiểm tra thay đổi.
4. Gửi Pull Request kèm mô tả rõ ràng.


---

