# Lab 12 - Production Research Agent

Ung dung nay giu nguyen bo khung production cua folder 06 va bo sung y tuong
Research Agent tu `sample/starter_v0`:

- Model co the tu chon tool.
- Tool result duoc dua lai model de tao cau tra loi cuoi.
- Agent stateless: moi request la mot run doc lap.
- Tool chi doc du lieu, khong gui/publish va khong ghi file.
- Auth, rate limit, cost guard, health check va deployment van theo folder 06.

## Kien truc

```text
Client
  -> API key authentication
  -> Rate limit
  -> Daily cost guard
  -> Research Agent
       -> Gemini model
       -> read-only tools
       -> final answer with sources
  -> JSON response
```

Khi khong co `GEMINI_API_KEY`, API van chay bang mock response. Tool calling chi
duoc bat khi co Gemini API key.

## Tool da tich hop

| Tool | Chuc nang | Can key |
|---|---|---|
| `web_search` | Tim web/tin tuc qua Tavily | `TAVILY_API_KEY` |
| `read_url` | Doc noi dung URL qua Firecrawl | `FIRECRAWL_API_KEY` |
| `search_papers` | Tim paper tren arXiv | Khong |
| `market_price` | Tra gia stock/crypto | Khong |
| `weather` | Tra thoi tiet hien tai | Khong |
| `summarize_text` | Tom tat extractive tai local | Khong |
| `format_digest` | Format ket qua thanh Markdown | Khong |

Khong mang sang cac tool `send`, Telegram, social post, image analyzer va
download PDF. Cac tool do co side effect, can them dich vu, hoac ghi file local
khong phu hop voi container stateless.

## Cau truc

```text
06-lab-complete/
├── app/
│   ├── main.py          # FastAPI, auth, rate limit, cost guard
│   ├── config.py        # Environment configuration
│   ├── agent.py         # Model/tool loop
│   └── tools.py         # Tool registry + implementations
├── utils/
│   └── mock_llm.py      # Offline fallback
├── Dockerfile
├── docker-compose.yml
├── railway.toml
├── render.yaml
├── .env.example
└── requirements.txt
```

## 1. Setup local

```bash
cd 06-lab-complete
cp .env.example .env.local
```

Tao secret local:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Mo `.env.local` va thay it nhat:

```dotenv
AGENT_API_KEY=gia-tri-vua-tao
JWT_SECRET=mot-gia-tri-random-khac
```

### Chay mock, khong ton API

De trong:

```dotenv
GEMINI_API_KEY=
```

Sau do:

```bash
docker compose up --build
```

### Chay Research Agent that

Them vao `.env.local`:

```dotenv
GEMINI_API_KEY=your-gemini-key
LLM_MODEL=gemini-2.5-flash
```

Tool web la tuy chon:

```dotenv
TAVILY_API_KEY=your-tavily-key
FIRECRAWL_API_KEY=your-firecrawl-key
```

Neu khong co Tavily/Firecrawl, agent van dung duoc arXiv, market, weather,
summarizer va formatter.

Khoi dong:

```bash
docker compose up --build
```

Neu khong dung Docker:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app \
  --env-file .env.local \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

## 2. Test local

Chay unit test:

```bash
python -m unittest discover -s tests -v
```

Test API:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/tools
```

Goi agent:

```bash
API_KEY=$(grep '^AGENT_API_KEY=' .env.local | cut -d= -f2-)

curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Tim 3 paper gan day ve AI agent"}'
```

Thu tool khac:

```bash
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Thoi tiet hien tai o Bangkok nhu the nao?"}'
```

Response co truong `tools_used`:

```json
{
  "question": "...",
  "answer": "...",
  "model": "...",
  "tools_used": [
    {
      "name": "weather",
      "arguments": {"location": "Bangkok"},
      "ok": true,
      "duration_ms": 421.7
    }
  ],
  "timestamp": "..."
}
```

## 3. Production readiness

```bash
python check_production_ready.py
```

Truoc khi deploy, dam bao:

- `.env.local` khong duoc commit.
- `AGENT_API_KEY` va `JWT_SECRET` la secret manh.
- `ENVIRONMENT=production`.
- `ALLOWED_ORIGINS` khong dung `*` neu API duoc goi tu browser.
- Dat spending limit trong Google AI Studio/Tavily/Firecrawl dashboard.
- `MAX_TOOL_ROUNDS=3` la muc khoi dau hop ly.

## 4. Deploy Railway - ban tu thuc hien

Khong chay cac lenh deploy tu repository root. Service phai dung
`06-lab-complete` lam root directory.

### Cach CLI

```bash
cd 06-lab-complete
railway login
railway init
```

Dat bien moi truong. Thay cac placeholder truoc khi chay:

```bash
railway variable set ENVIRONMENT=production --skip-deploys
railway variable set AGENT_API_KEY=YOUR_STRONG_AGENT_KEY --skip-deploys
railway variable set JWT_SECRET=YOUR_STRONG_JWT_SECRET --skip-deploys
railway variable set GEMINI_API_KEY=YOUR_GEMINI_KEY --skip-deploys
railway variable set LLM_MODEL=gemini-2.5-flash --skip-deploys
railway variable set MAX_TOOL_ROUNDS=3 --skip-deploys
railway variable set DAILY_BUDGET_USD=5.0 --skip-deploys
railway variable set INPUT_COST_PER_MILLION_USD=0.54 --skip-deploys
railway variable set OUTPUT_COST_PER_MILLION_USD=4.50 --skip-deploys
railway variable set RATE_LIMIT_PER_MINUTE=20 --skip-deploys
```

Tuy chon:

```bash
railway variable set TAVILY_API_KEY=YOUR_TAVILY_KEY --skip-deploys
railway variable set FIRECRAWL_API_KEY=YOUR_FIRECRAWL_KEY --skip-deploys
railway variable set ALLOWED_ORIGINS=https://your-frontend.example --skip-deploys
```

Deploy:

```bash
# Bat buoc voi monorepo: upload folder hien tai lam deployment root.
railway up . --path-as-root
railway domain
```

Khong dung `railway up` khong co `--path-as-root` trong repository nay. Railway
se upload repository root, khong thay `06-lab-complete/Dockerfile` va co the
fallback sang Railpack.

Khong dat **Custom Start Command** tren Railway Dashboard va khong them
`startCommand` vao `railway.toml`. Deployment Dockerfile phai dung `CMD` sau:

```dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2}"]
```

`sh -c` la phan thuc hien bien `${PORT}`. Neu Railway override bang mot exec
command chua `$PORT`, Uvicorn co the nhan chuoi literal `$PORT` va crash.

Kiem tra:

```bash
curl https://YOUR_RAILWAY_DOMAIN/health
curl https://YOUR_RAILWAY_DOMAIN/tools
```

Neu dung Railway Dashboard + GitHub:

1. Tao service tu GitHub repository.
2. Dat **Root Directory** la `/06-lab-complete`.
3. Them cac variables nhu danh sach tren.
4. Generate domain.
5. Push commit de Railway auto-deploy.

### Railway health check troubleshooting

Kiem tra deployment:

```bash
railway status --json
railway logs --lines 200
```

Trong build log dung, ban phai thay Railway dung `Dockerfile`, khong phai:

```text
using build driver railpack
Railpack could not determine how to build the app
```

Neu log co noi dung tren, Root Directory/upload root van dang sai.

Kiem tra public endpoint sau khi deployment co status `SUCCESS`:

```bash
railway domain
curl -i https://YOUR_RAILWAY_DOMAIN/health
```

Ket qua can co:

```text
HTTP/2 200
```

## 5. Deploy Render - ban tu thuc hien

`render.yaml` da co `rootDir: 06-lab-complete`.

1. Push code len GitHub.
2. Vao Render Dashboard.
3. Chon **New** -> **Blueprint**.
4. Ket noi repository.
5. Chon Blueprint file `06-lab-complete/render.yaml`.
6. Dien `GEMINI_API_KEY`.
7. Dien `TAVILY_API_KEY` va `FIRECRAWL_API_KEY` neu dung.
8. Render tu sinh `AGENT_API_KEY` va `JWT_SECRET`.
9. Chon **Apply** va doi deploy hoan tat.

Sau deploy, vao service **Environment** de xem/copy `AGENT_API_KEY`, sau do:

```bash
curl https://YOUR_RENDER_DOMAIN/health

curl -X POST https://YOUR_RENDER_DOMAIN/ask \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Tim tin AI agent trong tuan nay"}'
```

## 6. Theo doi sau deploy

- Xem `/health` va log request.
- Theo doi `429` de dieu chinh rate limit.
- Theo doi `503` de biet daily budget da het.
- Theo doi `502` de phat hien loi Gemini/provider.
- Kiem tra `tools_used` de debug routing.
- Khong log API key hay full tool content.

## Gioi han cua bai lab

- Rate limit va daily cost dang nam trong RAM cua tung worker.
- Nhieu worker/instance khong chia se cung bo dem.
- `REDIS_URL` da co san nhung rate limit chua dung Redis.
- Cost guard chi uoc luong token, khong thay the billing data cua provider.
- Cap nhat `INPUT_COST_PER_MILLION_USD` va `OUTPUT_COST_PER_MILLION_USD` khi
  Google thay doi bang gia hoac khi ban doi model.
- Public weather/market endpoints co the thay doi hoac rate limit.

De production nghiem tuc, chuyen rate limit va budget counter sang Redis,
them tracing, retry co backoff va metric tap trung.
