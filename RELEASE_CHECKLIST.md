# TaskFlow AI v1.0 — Checklist trước phát hành

## A. Bộ nguồn và dữ liệu

- [ ] Có đủ `main.py`, `agent.py`, `supervisor.py`, `security.py`.
- [ ] Có đủ `research_search.py`, `writing_agent.py`, `api_errors.py`, `usage_tracker.py` từ repository **hiện đang chạy tốt**.
- [ ] HTML/CSS/JS nằm trong `backend/frontend/` như cấu hình `StaticFiles` của `main.py`.
- [ ] Chạy `python backend/check_release.py` từ repo gốc bằng đúng venv không báo thiếu.
- [ ] `.env` chỉ lưu trên máy, `.gitignore` có hiệu lực và không có key trong Git history.
- [ ] Sao lưu các database (`tasks.db`, `chat_history.db`, `research_history.db`, `writing_history.db`, `usage_history.db`) cùng `data/documents/` và `chroma_db/` nếu có.

## B. Kiểm thử ứng viên v1.0

- [ ] Test Python: `python -m unittest discover -p "test_*.py" -v` tại `backend/` thành công.
- [ ] `GET /health` trả `{"status":"ok"}`.
- [ ] Dashboard cập nhật theo CRUD công việc và deadline.
- [ ] AI Chat lưu lịch sử và không lẫn ngữ cảnh hội thoại khác.
- [ ] Hỏi PDF theo đúng tài liệu chọn và dẫn tên file/trang đúng.
- [ ] Nghiên cứu web có nguồn, lưu và mở lại lịch sử.
- [ ] Soạn thảo lưu/chỉnh sửa/xuất TXT, DOCX, PDF tiếng Việt đúng dấu.
- [ ] Thống kê AI ghi lượt gọi mới, token và chi phí ước tính.
- [ ] Khung phóng to/thu nhỏ hoạt động và dữ liệu còn sau F5.
- [ ] Backend chỉ chạy localhost, không mở mạng ngoài.

Người dùng đã xác nhận **8/8 bài kiểm thử tích hợp** ngày 05/11/2026. Phải kiểm thử lại khi chuyển môi trường hoặc nâng cấp thư viện.

## C. Trước khi push/tag GitHub

- [ ] Kiểm tra `git status` và `git diff --cached --name-only`; không có `.env`, `.db`, PDF/CV riêng tư, chỉ mục hay backup.
- [ ] Nếu dữ liệu bí mật **đã được Git theo dõi**, `.gitignore` không tự gỡ chúng; xử lý riêng trước khi push.
- [ ] Tạo `requirements-lock.txt` từ venv **đã được kiểm thử** và rà soát URL nhạy cảm.
- [ ] Commit/push, kiểm tra commit trên GitHub; chỉ tạo tag v1.0 khi bộ nguồn thực sự hoàn chỉnh.

## D. Chưa đủ điều kiện mở ra Internet

- [ ] Xác thực và phân quyền bảo vệ API, SQLite, PDF, hội thoại, bản thảo.
- [ ] HTTPS, bảo vệ session/cookie, rate limiting, hạn mức gọi mô hình/chi phí.
- [ ] Tách dữ liệu theo người dùng, có quy trình lưu và xóa dữ liệu cá nhân.
- [ ] Cấu hình secrets, logging và giám sát không để lộ nội dung nhạy cảm.
- [ ] Backup/restore, kiểm tra bảo mật, kế hoạch cập nhật phụ thuộc.

Middleware localhost **không phải** giải pháp thay thế cho các mục này.

## E. Kiểm tra khả năng clone và chạy trên Windows sạch

- [ ] `requirements-lock.txt` đã được push cùng `SETUP.bat`, `START.bat`, `setup_local.py`, `app_launcher.py` và README mới.
- [ ] Clone repository vào **thư mục hoàn toàn mới** trên máy sạch, có Python 3.10.
- [ ] Chạy `SETUP.bat`: tạo `.venv`, cài thư viện, chạy `check_release.py` và nhập **API key riêng của người chạy**.
- [ ] Xác nhận `backend/.env` được tạo cục bộ và **không bị Git theo dõi** (`git status --ignored`).
- [ ] Chạy `START.bat`, trình duyệt tự mở `http://127.0.0.1:8000/ui/`.
- [ ] Kiểm thử AI Chat và CRUD nhiệm vụ thật. Thử Nghiên cứu web nếu đã cấu hình Tavily.
- [ ] Đóng và mở lại bằng `START.bat`: không cần cài lại hay nhập lại key.
- [ ] Xác nhận API key không xuất hiện trong GitHub, log, ảnh chụp hay README.
