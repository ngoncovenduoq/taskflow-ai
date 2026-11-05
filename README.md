# TaskFlow AI — v1.0 release candidate (localhost)

TaskFlow AI là trợ lý AI cá nhân chạy trên FastAPI, SQLite và giao diện HTML/CSS/JavaScript thuần. Các tính năng: quản lý công việc/deadline, AI Chat và lịch sử, hỏi đáp PDF với ChromaDB, nghiên cứu web, soạn thảo/xuất tài liệu và thống kê token/chi phí.

> **Trạng thái:** Ứng viên v1.0 để thử trên máy cá nhân, **chưa phải bản triển khai công khai**. Người dùng đã xác nhận 8/8 bài kiểm thử tích hợp ngày 05/11/2026. Chưa có đăng nhập/phân quyền cho nhiều người dùng.

## 1. Cấu trúc repository

Trong repository chạy thật, giao diện phải nằm **trong** `backend/frontend`:

```text
taskflow-ai/
├── README.md
├── requirements.txt
├── RELEASE_CHECKLIST.md
├── .gitignore
└── backend/
    ├── main.py
    ├── agent.py
    ├── supervisor.py
    ├── security.py
    ├── research_search.py
    ├── writing_agent.py
    ├── api_errors.py
    ├── usage_tracker.py
    ├── check_release.py
    ├── .env.example
    ├── ... các API, kho SQLite và test khác ...
    └── frontend/
        ├── index.html
        ├── app.js
        └── *.css
```

**Lưu ý về bản sao trong ChatGPT:** `frontend/` hiện đang nằm ngang cấp `backend/` để kiểm thử UI và thiếu bốn module `research_search.py`, `writing_agent.py`, `api_errors.py`, `usage_tracker.py`. Chúng có thể đã tồn tại trong repository trên máy Quân. Xác nhận bằng `check_release.py`; không chép đè các module hiện chạy tốt bằng bản cũ chỉ để đủ danh sách.

## 2. Cài đặt Windows (PowerShell)

Khuyến nghị Python 3.12, cùng phiên bản đã chạy trên máy Quân. Trong thư mục gốc repository:

**Nếu Quân đã có `.venv` đang chạy tốt, không cài lại thư viện trong môi trường đó.** Các lệnh dưới đây dành cho lần cài mới hoặc một môi trường thử nghiệm riêng; dùng `requirements-lock.txt` đã được kiểm thử khi có thể.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` liệt kê thư viện trực tiếp nhưng **chưa khóa phiên bản**; bản sao hiện tại không có dữ liệu phiên bản từ môi trường Windows đã chạy thành công. Sau khi kiểm thử ổn định trên máy, tạo bản khóa:

```powershell
.\.venv\Scripts\python.exe -m pip freeze > requirements-lock.txt
```

Rà soát `requirements-lock.txt` xem có URL chứa thông tin đăng nhập không trước khi commit. Không tự nâng cấp tất cả thư viện của bản đang hoạt động mà chưa kiểm thử lại.

## 3. Cấu hình riêng tư

```powershell
Copy-Item backend\.env.example backend\.env
```

Sửa `backend/.env` **trên máy cá nhân**, thay các chuỗi mẫu bằng key OpenRouter và (nếu dùng) Tavily thật. Không nhập key trong frontend, commit `.env` hoặc gửi key trong chat.

## 4. Kiểm tra trước khi chạy

Từ thư mục gốc, dùng đúng venv:

```powershell
.\.venv\Scripts\python.exe backend\check_release.py
```

Script chỉ kiểm tra file/thư viện và sự hiện diện của cấu hình, **không đọc hay in API key** và không gọi mô hình. Nếu thiếu module, bổ sung từ bộ nguồn hiện tại trước khi đóng gói.

Chạy unit test:

```powershell
cd backend
..\.venv\Scripts\python.exe -m unittest discover -p "test_*.py" -v
```

## 5. Khởi động trên localhost

Từ thư mục `backend`:

```powershell
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- Giao diện: http://127.0.0.1:8000/ui/
- Kết nối: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs

Khi thay CSS/JS, nhấn `Ctrl + F5`. Kiểm tra các tính năng theo `RELEASE_CHECKLIST.md`.

## 6. Dữ liệu, chi phí và giới hạn hiện tại

- SQLite và ChromaDB giữ dữ liệu cục bộ. **Không xóa** `.db`, tài liệu hoặc chỉ mục khi cập nhật code.
- PDF văn bản tối đa 5 MB, chưa hỗ trợ OCR bản scan.
- OpenRouter/Tavily có thể phát sinh chi phí. Con số trong Phân tích AI chỉ là **ước tính**, không phải hóa đơn.
- Lịch sử sử dụng AI chỉ lưu các lượt gọi kể từ khi bật thống kê.
- Giao diện chạy không cần Node.js; Node chỉ để chạy bài kiểm thử mock tùy chọn.
- Middleware `security.py` giới hạn nguồn trình duyệt và Host localhost, **không thay thế xác thực**. Không mở `--host 0.0.0.0` khi chưa có cơ chế bảo vệ phù hợp.
- Phiên cải thiện trạng thái tải và xử lý lỗi đã được Quân chọn **bỏ qua**.

## 7. Triển khai thật

Chỉ xem xét triển khai công khai sau khi có xác thực/phân quyền, HTTPS, kiểm soát tần suất gọi AI, sao lưu, tách dữ liệu người dùng và kiểm tra bảo mật. Xem checklist phát hành để biết các bước chưa hoàn thành.
