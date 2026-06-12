# Section 1 — Từ Localhost Đến Production

## Mục tiêu học
- Hiểu tại sao "it works on my machine" là vấn đề
- Nhận ra sự khác biệt giữa dev và production environment
- Áp dụng 4 nguyên tắc 12-factor cơ bản

---

## Ví dụ Basic — Agent "Kiểu Localhost"

```
develop/
├── app.py          # ❌ Anti-patterns: hardcode secrets, no config, no health check
└── requirements.txt
```

### Chạy thử
```bash
cd develop
pip install -r requirements.txt
python app.py
# Truy cập: http://localhost:8000
```

### Những vấn đề trong code này:
1. API key hardcode trong code
2. Không có health check endpoint
3. Debug mode bật cứng
4. Không xử lý SIGTERM gracefully
5. Config không đến từ environment

---

## Ví dụ Advanced — 12-Factor Compliant Agent

```
production/
├── app.py          # ✅ Clean: config from env, health check, graceful shutdown
├── config.py       # ✅ Centralized config management
├── .env.example    # ✅ Template — không commit .env thật
└── requirements.txt
```

### Chạy thử
```bash
cd production
pip install -r requirements.txt
cp .env.example .env
# Sửa .env nếu cần
python app.py
```

### So sánh với Basic:

| | Basic (❌) | Advanced (✅) |
|--|-----------|--------------|
| Config | Hardcode trong code | Đọc từ env vars |
| Secrets | `api_key = "sk-abc123"` | `os.getenv("OPENAI_API_KEY")` |
| Port | Cố định `8000` | Từ `PORT` env var |
| Health check | Không có | `GET /health` |
| Shutdown | Tắt đột ngột | Graceful — hoàn thành request hiện tại |
| Logging | `print()` | Structured JSON logging |

---

## Câu hỏi thảo luận

# Discussion Questions – From Localhost to Production

## 1. Điều gì xảy ra nếu bạn push code với API key hardcode lên GitHub public?

Nếu API key bị hardcode và được push lên GitHub public, bất kỳ ai cũng có thể nhìn thấy và sử dụng key đó.

### Hậu quả

* Người khác có thể sử dụng tài khoản API của bạn.
* Phát sinh chi phí ngoài ý muốn nếu đó là dịch vụ trả phí (OpenAI, AWS, Google Cloud, v.v.).
* Kẻ xấu có thể dùng key để gửi request độc hại hoặc truy cập dữ liệu.
* Nhiều nhà cung cấp sẽ tự động thu hồi (revoke) key khi phát hiện bị lộ.
* Nếu key có quyền cao, có thể dẫn đến mất hoặc rò rỉ dữ liệu.

## 2. Tại sao stateless quan trọng khi scale?

Stateless nghĩa là server không lưu trạng thái người dùng trong bộ nhớ cục bộ của chính nó.

Nếu request đầu tiên đi vào Server A nhưng request tiếp theo được chuyển sang Server B, ứng dụng vẫn hoạt động bình thường vì dữ liệu được lưu ở nơi dùng chung (Database, Redis, S3, v.v.).

### Lợi ích

* Dễ mở rộng hệ thống bằng cách thêm nhiều server.
* Dễ thay thế server bị lỗi.
* Hỗ trợ auto-scaling trên cloud.
* Giúp triển khai phiên bản mới mà không làm gián đoạn người dùng.
* Tăng khả năng chịu lỗi của hệ thống.

---

## 3. 12-Factor nói "dev/prod parity" nghĩa là gì trong thực tế?

Dev/Prod Parity là nguyên tắc cho rằng môi trường phát triển (development) và môi trường production nên giống nhau càng nhiều càng tốt.

Mục tiêu là tránh tình huống:

> "Chạy trên máy em thì được."

### Ví dụ không tốt

| Development    | Production  |
| -------------- | ----------- |
| SQLite         | PostgreSQL  |
| Windows        | Linux       |
| Python 3.10    | Python 3.13 |
| Chạy trực tiếp | Docker      |

Điều này dễ gây ra lỗi khi deploy do sự khác biệt môi trường.

### Ví dụ tốt

| Development              | Production               |
| ------------------------ | ------------------------ |
| PostgreSQL               | PostgreSQL               |
| Docker                   | Docker                   |
| Python 3.12              | Python 3.12              |
| Cùng cấu hình môi trường | Cùng cấu hình môi trường |

### Lợi ích

* Phát hiện lỗi sớm hơn.
* Giảm rủi ro khi triển khai.
* Tăng độ tin cậy của hệ thống.
* Hạn chế các lỗi phát sinh do khác biệt môi trường.