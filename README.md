# TaskFlow AI

Trợ lý AI cá nhân chạy trên máy người dùng: quản lý công việc/deadline, AI Chat và lịch sử hội thoại, hỏi đáp nhiều PDF (RAG), nghiên cứu web, soạn thảo/xuất tài liệu và phân tích token/chi phí. Backend dùng FastAPI + SQLite + ChromaDB; frontend dùng HTML/CSS/JavaScript.

**Trạng thái:** bản v1.0 chạy cục bộ (localhost), chưa có đăng nhập/phân quyền để đưa lên Internet. Trên máy tác giả, 41 unit test và 8 bài kiểm thử tích hợp đã đạt (05/11/2026). Mỗi máy clone cần kiểm tra lại.

## Clone và chạy trên Windows

**Chuẩn bị:** cài Git và **Python 3.10** (có Python Launcher `py`), có Internet để tải thư viện và gọi AI. Bạn cần **OpenRouter API key của mình** để sử dụng AI thật. Nếu muốn nghiên cứu web, cần thêm Tavily API key.

1. Mở PowerShell, chạy (thay URL bằng URL repository thật):

   ```powershell
   git clone https://github.com/USERNAME/taskflow-ai.git
   cd taskflow-ai
   ```

2. Nhấp đúp **`SETUP.bat`** tại thư mục gốc. Chương trình tự tạo `.venv`, cài thư viện và kiểm tra cấu trúc. Khi được hỏi, nhập OpenRouter API key (ký tự không hiển thị); Tavily key có thể để trống. Việc cài đặt chỉ cần làm một lần.
3. Nhấp đúp **`START.bat`**. Chờ trình duyệt mở **http://127.0.0.1:8000/ui/**.
4. Thử tạo công việc, trò chuyện AI hoặc tải PDF. Để tắt ứng dụng, nhấn `Ctrl+C` ở cửa sổ đang chạy.

> **Bảo mật:** API key lưu cục bộ trong `backend/.env` dưới dạng văn bản và file đã được `.gitignore` bỏ qua. Không chia sẻ file này, không commit lên GitHub. Người clone dùng key của **chính họ**; dự án không kèm key của tác giả. Nếu tác giả muốn cung cấp quyền truy cập API cho người khác mà **không cần cấp key**, phải triển khai backend riêng có xác thực và hạn mức — không thể an toàn bằng cách nhúng key vào một repo công khai.

`SETUP.bat` ưu tiên `requirements-lock.txt` (được tạo từ môi trường đã kiểm thử). Nếu không có, script dùng `requirements.txt` chưa khóa phiên bản và cảnh báo. **Tác giả cần commit `requirements-lock.txt` lên GitHub** để người clone có môi trường sát bản đã kiểm thử.

## Chạy thủ công bằng PowerShell

Nếu không muốn dùng `.bat`, mở PowerShell tại thư mục repo:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe backend\check_release.py
.\.venv\Scripts\python.exe setup_local.py
.\.venv\Scripts\python.exe app_launcher.py
```

Nếu không có `requirements-lock.txt`, dùng `requirements.txt` thay thế, rồi kiểm tra tính tương thích. Muốn tự cấu hình mà không chạy wizard, sao chép `backend/.env.example` thành `backend/.env`, thay `OPENROUTER_API_KEY` bằng key thật và bỏ trống `TAVILY_API_KEY` nếu không dùng Nghiên cứu web.

Để xem log backend bằng cách chạy trực tiếp:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Trang web: http://127.0.0.1:8000/ui/ · Health: http://127.0.0.1:8000/health · API Docs: http://127.0.0.1:8000/docs

## Kiểm tra sau khi clone

Trong thư mục repo:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v
```

Sau đó kiểm tra trực tiếp:

- Truy cập `/health` thấy `{"status":"ok"}`.
- Tạo và hoàn thành một công việc; Dashboard cập nhật.
- Gửi câu hỏi trong AI Chat, mở lại lịch sử và nhấn F5.
- Tải PDF văn bản (tối đa 5 MB), hỏi thông tin và xem dẫn nguồn.
- Nghiên cứu web nếu đã điền Tavily key.
- Soạn thảo, chỉnh sửa và xuất TXT/DOCX/PDF; kiểm tra Phân tích AI.

## Cấu trúc cần có trong GitHub

```text
taskflow-ai/
├── SETUP.bat                # Cài trên Windows
├── START.bat                # Chạy ứng dụng
├── setup_local.py
├── app_launcher.py
├── requirements-lock.txt   # Nên có: khóa phiên bản đã test
├── requirements.txt
├── .gitignore
└── backend/
    ├── main.py
    ├── agent.py
    ├── supervisor.py
    ├── research_search.py
    ├── writing_agent.py
    ├── api_errors.py
    ├── usage_tracker.py
    ├── .env.example
    ├── ... các module và test khác ...
    └── frontend/
        ├── index.html
        ├── app.js
        └── *.css
```

**Quan trọng:** `frontend/` phải nằm trong **`backend/frontend/`**; `main.py` phục vụ giao diện tại đường dẫn này. Không đưa `.env`, `.db`, tài liệu PDF riêng tư, chỉ mục Chroma, hay `.venv` lên Git.

## Giới hạn hiện tại

- Chạy cục bộ tại `127.0.0.1`; không mở `0.0.0.0` khi chưa có xác thực, phân quyền và biện pháp bảo vệ.
- AI Chat/OpenRouter và Nghiên cứu web/Tavily cần Internet và key hợp lệ, có thể phát sinh chi phí.
- PDF scan chưa hỗ trợ OCR; lịch sử và dữ liệu SQLite/ChromaDB được lưu trên máy đang sử dụng, mỗi máy độc lập.
- Thống kê chi phí AI là ước tính, không phải hóa đơn.

Xem [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) để kiểm tra trước khi công bố bản mới.
