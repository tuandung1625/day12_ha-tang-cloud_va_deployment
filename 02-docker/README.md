# Section 2 — Docker: Đóng Gói Agent Thành Container

## Mục tiêu học
- Hiểu container là gì và tại sao cần nó
- Viết Dockerfile đúng cách (single vs multi-stage)
- Dùng Docker Compose để chạy multi-service stack
- Tối ưu image size xuống dưới 500 MB

---

## Ví dụ Basic — Dockerfile Đơn Giản

```
develop/
├── app.py
├── Dockerfile          # Single-stage, dễ hiểu
├── .dockerignore
└── requirements.txt
```

### Chạy thử
```bash
# IMPORTANT: Build from project root!
cd ../..  # Go to project root

# Build image
docker build -f 02-docker/develop/Dockerfile -t agent-develop .

# Xem size
docker images agent-develop

# Chạy container
# -p 8000:8000 : map port 8000 của máy host → port 8000 trong container
# -d           : chạy ở chế độ detached (nền), terminal không bị block
# agent-develop: tên image đã build ở bước trên
docker run -p 8000:8000 -d agent-develop

# Xem container đang chạy
docker ps

# Truy cập vào bên trong container đang chạy (mở shell tương tác)
# -i: giữ kết nối stdin mở | -t: cấp terminal giả (pseudo-TTY)
# Hữu ích để debug, kiểm tra file, xem log, hoặc chạy lệnh trực tiếp trong container

docker exec -it <container-id> sh

# Test
curl http://localhost:8000/health
```

---

## Ví dụ Advanced — Multi-Stage + Docker Compose

```
production/
├── app.py
├── Dockerfile              # Multi-stage build → image nhỏ hơn nhiều
├── docker-compose.yml      # Full stack: agent + vector store + redis
├── nginx/
│   └── nginx.conf          # Reverse proxy
├── .dockerignore
└── requirements.txt
```

### Chạy thử
```bash
# From project root
cd ../..  # if not already there

# Khởi động toàn bộ stack (1 lệnh!)
docker compose -f 02-docker/production/docker-compose.yml up

# Xem các service đang chạy
docker compose -f 02-docker/production/docker-compose.yml ps

# Test agent qua Nginx
curl http://localhost/health

# Dừng toàn bộ
docker compose -f 02-docker/production/docker-compose.yml down
```

### So sánh image size:

```bash
# Basic vs Advanced
docker images | grep agent
# agent-basic    ~  800 MB  ← python:3.11 base
# agent-advanced ~  160 MB  ← python:3.11-slim + multi-stage
```

---

## Lý thuyết: Tại Sao Multi-Stage?

```dockerfile
# Stage 1: Builder — có đầy đủ tools để compile deps
FROM python:3.11 AS builder   # 1 GB
RUN pip install ...            # thêm deps vào layer này

# Stage 2: Runtime — chỉ copy những gì cần chạy
FROM python:3.11-slim          # 150 MB ← bắt đầu từ image sạch
COPY --from=builder ...        # copy chỉ /site-packages
```

**Kết quả:** Final image chỉ có runtime, không có pip, không có build tools → nhỏ và an toàn hơn.

---

## Câu hỏi thảo luận

# 1. Tại sao COPY requirements.txt rồi RUN pip install TRƯỚC khi COPY . . ?

Docker build theo từng layer và có cache.

Ví dụ:

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

Nếu chỉ sửa source code:

app.py
routes.py

thì layer pip install vẫn được cache.

Docker chỉ chạy lại:

COPY . .

=> build rất nhanh.

Nếu làm ngược lại:

COPY . .
RUN pip install -r requirements.txt

thì mỗi lần sửa 1 dòng code Docker phải cài lại toàn bộ dependencies.

=> build rất chậm.

# 2. .dockerignore nên chứa những gì? Tại sao venv/ và .env quan trọng?

.dockerignore tương tự .gitignore.

Nó ngăn Docker copy các file không cần thiết vào image.

Ví dụ:

__pycache__/
*.pyc
.git/
venv/
.env
node_modules/
dist/
build/

Lý do:

- venv/
  Chứa Python packages trên máy local.
  Docker sẽ tự cài lại dependencies.
  Copy venv vào image vừa nặng vừa dễ lỗi.

- .env
  Chứa secrets:

  OPENAI_API_KEY=...
  DATABASE_PASSWORD=...

  Nếu copy vào image:
  - image to hơn
  - có nguy cơ lộ API key
  - ai pull image cũng thấy được

# 3. Nếu agent cần đọc file từ disk, làm sao mount volume vào container?

Dùng volume mount.

Ví dụ:

docker run \
  -v $(pwd)/data:/app/data \
  agent-develop

Ý nghĩa:

Host:
./data

↓

Container:
/app/data

Container đọc:

/app/data/file.txt

thì thực chất đang đọc:

./data/file.txt

trên máy thật.

Ví dụ:

Host:
D:\Documents\data\report.pdf

docker run \
  -v D:\Documents\data:/app/data \
  agent-develop

Trong container:

/app/data/report.pdf

sẽ là file report.pdf trên máy Windows của bạn.
