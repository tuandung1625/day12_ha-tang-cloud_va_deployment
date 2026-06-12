# Section 3 — Cloud Deployment Options

## 3 Tier: Chọn Platform Theo Nhu Cầu

| Tier | Platform | Khi nào dùng | Thời gian deploy |
|------|----------|-------------|-----------------|
| 1 | Railway, Render | MVP, demo, học | < 10 phút |
| 2 | AWS ECS, Cloud Run | Production | 15–30 phút |
| 3 | Kubernetes | Enterprise, large-scale | Vài giờ setup |

---

## railway/ — Deploy < 5 Phút

Không cần server config. Kết nối GitHub → Auto deploy.

```
railway/
├── railway.toml        # Railway config
├── Procfile            # Define start command
├── app.py              # Agent (Railway-ready)
└── requirements.txt
```

### Các bước deploy Railway:
```bash
cd 03-cloud-deployment/railway

# Chạy local trước
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Terminal khác:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Deployment là gì?"}'
```

Deploy:

```bash
railway login
railway init
railway up
railway domain
```

Nếu deploy bằng GitHub thay vì CLI, đặt **Root Directory** của Railway service
là `/03-cloud-deployment/railway`.

---

## render/ — render.yaml (Infrastructure as Code)

Định nghĩa toàn bộ infrastructure trong 1 YAML file.

```
render/
├── render.yaml         # Khai báo service, env vars, disk
├── app.py
└── requirements.txt
```

### Các bước deploy Render

1. Push repository lên GitHub.
2. Render Dashboard → **New** → **Blueprint**.
3. Kết nối repository.
4. Chọn Blueprint path là `03-cloud-deployment/render/render.yaml`.
5. Review rồi chọn **Apply**.

Test URL sau khi deploy:

```bash
curl https://YOUR-SERVICE.onrender.com/health
curl -X POST https://YOUR-SERVICE.onrender.com/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Render là gì?"}'
```

---

## production-cloud-run/ — GCP Cloud Run + CI/CD

Production-grade. Tự động build và deploy khi push code.

```
production-cloud-run/
├── app.py              # FastAPI app
├── Dockerfile          # Container image
├── requirements.txt
├── tests/              # Test chạy trước khi build
├── cloudbuild.yaml     # CI/CD pipeline
├── service.yaml        # Cloud Run service definition
└── README.md           # Hướng dẫn chi tiết
```

Làm theo [production-cloud-run/README.md](production-cloud-run/README.md).

> Gợi ý: học nhanh thì bắt đầu với Railway. Chọn Render nếu muốn deploy qua
> GitHub Blueprint. Chọn Cloud Run khi cần IAM, autoscaling và CI/CD trên GCP.

---

## Câu hỏi thảo luận


AI agent có thể cần:

- Chạy lâu nhiều bước
- Gọi LLM nhiều lần
- Gọi tool/API bên ngoài
- Giữ trạng thái hội thoại
- Streaming response về frontend
- Xử lý background task
- Kết nối database/vector database

Vì vậy, serverless có thể gặp vấn đề