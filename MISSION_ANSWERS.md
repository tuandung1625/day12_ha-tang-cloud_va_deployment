# Day 12 Lab - Mission Answers

**Student:** Nguyen Tuan Dung  
**Student ID:** 2A202600848  
**Date:** June 12, 2026  
**Final application:** `06-lab-complete/`  
**Platform:** Railway  
**Public URL:** <https://ntdungtest-826c.up.railway.app/>

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

The following problems exist in `01-localhost-vs-production/develop/app.py`:

1. The API key is hardcoded in source code.
2. The database URL includes a hardcoded username and password.
3. Secrets are printed to application logs.
4. Configuration values such as `DEBUG` and `MAX_TOKENS` are hardcoded.
5. The server binds to `localhost`, so it cannot receive traffic from outside
   the container.
6. Port `8000` is fixed instead of reading the platform-provided `PORT`.
7. Auto-reload is always enabled.
8. There is no `/health` endpoint.
9. There is no `/ready` endpoint.
10. The application uses `print()` instead of structured logging.
11. Input is not validated using a request model.
12. There is no graceful shutdown or resource cleanup.

If a real hardcoded key is pushed to a public GitHub repository, another person
can use it, create unexpected charges, access protected resources, or cause the
provider to revoke the key.

### Exercise 1.2: Basic version observations

The basic application can run locally and return mock agent responses, but that
only proves the business handler works. It is not production-ready because its
network binding, configuration, secrets, logging, health checks, and shutdown
behavior do not satisfy a cloud runtime.

### Exercise 1.3: Develop vs production comparison

| Feature | Develop | Production | Why Important? |
|---|---|---|---|
| Configuration | Hardcoded values | Environment variables in `config.py` | The same image can run in development, staging, and production |
| Secrets | Stored and logged in code | Injected at runtime | Prevents secrets from entering Git history and images |
| Host | `localhost` | `0.0.0.0` | Containers must listen on all interfaces |
| Port | Fixed `8000` | Reads `PORT` | Railway assigns the runtime port |
| Health check | Missing | `GET /health` | The platform can detect and replace an unhealthy instance |
| Readiness | Missing | `GET /ready` | Traffic is sent only after startup is complete |
| Logging | `print()` | Structured JSON events | Logs are searchable and machine-readable |
| Input validation | Minimal | Pydantic model and length limits | Rejects invalid or excessive input early |
| Shutdown | Abrupt | Lifespan and SIGTERM handling | Reduces dropped requests during deployment |
| Debug mode | Always enabled | Controlled by environment | Avoids reload and debug behavior in production |

`06-lab-complete` follows the production approach and also adds API
authentication, rate limiting, cost protection, security headers, Gemini and a
read-only tool registry.

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image:** The basic Dockerfile uses `python:3.11`. The final production
   image uses `python:3.11-slim`.
2. **Working directory:** `/app`.
3. **Why copy `requirements.txt` first?** Docker can reuse the dependency layer
   when only application source code changes. Dependencies are reinstalled only
   when `requirements.txt` changes.
4. **CMD vs ENTRYPOINT:** `CMD` supplies a default command and is easy to
   override. `ENTRYPOINT` defines the main executable and normally treats
   runtime arguments as parameters to that executable.

The final Dockerfile uses:

```dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2}"]
```

The shell wrapper is required so `${PORT}` is expanded correctly on Railway.
Railway does not override this command with a custom start command.

### Exercise 2.2: Build and run

Commands used for the basic example:

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
docker run --rm -p 8000:8000 my-agent:develop
curl http://localhost:8000/health
```

Useful debugging commands:

```bash
docker ps
docker logs CONTAINER_ID
docker exec -it CONTAINER_ID sh
```

### Exercise 2.3: Multi-stage build

- **Builder stage:** installs Python dependencies into a separate installation
  prefix.
- **Runtime stage:** starts from a clean slim image and copies only installed
  dependencies plus application source code.
- **Why smaller and safer:** compiler packages, build caches, source-control
  files, local virtual environments, and secrets are not included in the final
  runtime image.
- The final container runs as the non-root user `agent`.

Measurements supplied in the delivery checklist:

- Develop image: `1660 MB`
- Production image: `236 MB`
- Reduction: `85.78%`
- Production image requirement: below `500 MB` - passed by the recorded result.

### Exercise 2.4: Docker Compose architecture

The production Docker example contains Agent, Redis, Qdrant, and Nginx:

```text
Client
  |
  v
Nginx :80/:443
  |
  v
Agent :8000
  |            \
  v             v
Redis :6379   Qdrant :6333
```

- Nginx is the public reverse proxy.
- Agent instances are private services.
- Redis stores shared cache or session data.
- Qdrant stores vectors for RAG.
- Docker health checks and `depends_on` control startup dependencies.
- Services communicate by Compose DNS names such as `redis` and `qdrant`.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

**Result:** Deployed successfully.

**URL:** <https://ntdungtest-826c.up.railway.app/>

The Railway service uses:

- Root Directory: `/06-lab-complete`
- Dockerfile deployment
- Dockerfile `CMD`, with no custom Railway start command
- Health path: `/health`
- Health timeout: 120 seconds
- Runtime secrets configured through Railway variables

Public verification performed on June 12, 2026:

```text
GET /        -> 200 OK
GET /health  -> 200 OK
GET /ready   -> 200 OK
GET /tools   -> 200 OK
POST /ask without X-API-Key -> 401 Unauthorized
POST /ask with valid X-API-Key -> 200 OK
```

Health response:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "llm": "gemini",
    "tools": 7
  }
}
```

Authenticated agent response:

```json
{
  "question": "Reply exactly: DEPLOYMENT_OK",
  "answer": "DEPLOYMENT_OK",
  "model": "gemini-2.5-flash",
  "tools_used": []
}
```

No screenshot is currently stored in the repository. Railway dashboard and
public endpoint screenshots should be added under `screenshots/` before final
submission if screenshots are mandatory.

### Exercise 3.2: Railway vs Render configuration

| Area | Railway | Render |
|---|---|---|
| Configuration file | `railway.toml` | `render.yaml` |
| Build | Dockerfile builder | Docker runtime |
| Monorepo location | Dashboard Root Directory | `rootDir: 06-lab-complete` |
| Health check | `healthcheckPath` | `healthCheckPath` |
| Secrets | Railway Variables | `sync: false` environment variables |
| Generated secrets | Set manually or generated externally | `generateValue: true` |
| Deployment trigger | CLI or GitHub | Blueprint and GitHub auto-deploy |

Railway is used for the submitted deployment. Render remains an alternative
Infrastructure-as-Code configuration.

### Exercise 3.3: GCP Cloud Run CI/CD

The Cloud Run example follows this pipeline:

```text
Cloud Build test
  -> build Docker image
  -> push image to Artifact Registry
  -> deploy revision to Cloud Run
```

`cloudbuild.yaml` defines CI/CD commands. `service.yaml` defines service
resources, scaling, environment variables, probes, timeout and container port.
Cloud Run was studied but was not used for the final public deployment.

---

## Part 4: API Security

### Exercise 4.1: API key authentication

`X-API-Key` is read by FastAPI's `APIKeyHeader`. `verify_api_key()` compares it
with `AGENT_API_KEY`.

- Missing or invalid key: `401`.
- Valid key: request continues to rate limiting, cost guard and the agent.
- Rotation: generate a new secret, update the Railway variable, redeploy, then
  remove the old key from clients.

Verified public result:

```text
POST /ask without key -> 401
POST /ask with valid key -> 200
```

No secret values are included in this report.

### Exercise 4.2: JWT authentication

The advanced API Gateway example implements JWT in
`04-api-gateway/production/auth.py`:

1. User submits credentials.
2. Server creates an HS256 token containing `sub`, `role`, `iat`, and `exp`.
3. Client sends `Authorization: Bearer TOKEN`.
4. Server verifies signature and expiry.
5. Invalid or expired tokens return `401` or `403`.

The final Railway endpoint currently uses API-key authentication, not the JWT
flow. JWT remains implemented as an advanced exercise module.

### Exercise 4.3: Rate limiting

The algorithm is a **sliding window log** implemented with a deque of request
timestamps:

1. Remove timestamps older than 60 seconds.
2. Reject when the number of active timestamps reaches the limit.
3. Otherwise append the current timestamp.

The advanced exercise defines:

- Normal user: 10 requests/minute.
- Admin: 100 requests/minute.
- Admin bypass is implemented by selecting the larger admin limiter based on
  the authenticated role.

The final app uses the same algorithm and returns `429` with `Retry-After`, but
its current default is `20 requests/minute` and it stores counters in process
memory. For exact final-project compliance, configure
`RATE_LIMIT_PER_MINUTE=10` and move counters to Redis.

### Exercise 4.4: Cost guard

The final implementation:

1. Estimates input and output tokens.
2. Converts them to estimated Gemini cost using environment-configurable prices.
3. Accumulates estimated daily cost.
4. Rejects further calls with `503` after `DAILY_BUDGET_USD` is exhausted.
5. Exposes protected budget statistics at `/metrics`.

Relevant variables:

```dotenv
DAILY_BUDGET_USD=5.0
INPUT_COST_PER_MILLION_USD=0.54
OUTPUT_COST_PER_MILLION_USD=4.50
```

This protects the demo from uncontrolled spending, but it is not the exact
`$10/month per user in Redis` implementation requested by the final-project
rubric. Production completion requires a key such as
`budget:{user_id}:{YYYY-MM}` in Redis with a monthly TTL.

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health and readiness checks

- `/health` is the liveness endpoint. It returns status, version, environment,
  uptime, request count, active LLM provider and tool count.
- `/ready` is the readiness endpoint. It returns `200` only after application
  startup completes and returns `503` when `_is_ready` is false.

Verified on Railway:

```text
GET /health -> 200 OK, status=ok
GET /ready  -> 200 OK, ready=true
```

### Exercise 5.2: Graceful shutdown

The final application:

- registers a SIGTERM handler;
- uses FastAPI lifespan startup/shutdown hooks;
- changes readiness to false during shutdown;
- runs Uvicorn, which handles graceful request completion.

The dedicated `05-scaling-reliability/develop` example additionally tracks
in-flight requests and waits up to 30 seconds before shutdown.

Expected flow:

```text
SIGTERM
  -> stop advertising readiness
  -> stop accepting new traffic
  -> finish in-flight requests
  -> run lifespan cleanup
  -> exit
```

### Exercise 5.3: Stateless design

The research-agent request itself is stateless: each `/ask` call creates a new
Gemini/tool loop and does not keep conversation history.

The dedicated production scaling example stores conversation history in Redis:

```text
session:{session_id} -> serialized conversation history, TTL 3600 seconds
```

This allows any Agent instance to continue the same session.

Important limitation: rate-limit counters and budget counters in
`06-lab-complete` are still stored in process memory. Therefore the final app
is stateless for agent conversations, but not fully distributed for operational
counters. Redis migration is still required for strict rubric compliance.

### Exercise 5.4: Load balancing

The scaling exercise architecture is:

```text
Client
  -> Nginx :8080
      -> Agent instance 1
      -> Agent instance 2
      -> Agent instance 3
           |
           v
         Redis
```

Nginx uses the `agent:8000` Compose service name and Docker DNS. Requests are
distributed across scaled Agent containers. `proxy_next_upstream` retries
another instance after an error, timeout, or HTTP 503.

Command:

```bash
cd 05-scaling-reliability/production
docker compose up --scale agent=3
```

The final Railway submission currently runs as a single Railway service and
does not expose the Nginx/three-instance demo publicly.

### Exercise 5.5: Stateless test

`05-scaling-reliability/production/test_stateless.py` performs these checks:

1. Creates a conversation session.
2. Sends five requests using the same `session_id`.
3. Records the `served_by` instance for each response.
4. Fetches session history after requests reach different instances.
5. Confirms all messages remain available through Redis.

Expected successful result:

```text
All requests served despite different instances.
Session history preserved across all instances via Redis.
```

The script and implementation are present, but no fresh Docker execution output
or screenshot is included in this report.

---

## Final Project Implementation Summary

| Requirement | Status | Evidence / Limitation |
|---|---|---|
| REST agent | Passed | Authenticated `/ask` returned `200` on Railway |
| Gemini agent | Passed | `gemini-2.5-flash` verified |
| Tool calling | Passed | Seven read-only tools registered |
| Multi-stage Dockerfile | Passed | Builder/runtime stages and non-root user |
| Environment configuration | Passed | `app/config.py` and Railway variables |
| API key authentication | Passed | Public no-key request returned `401` |
| Rate limiting | Partial | Implemented in memory; default is 20/min, rubric asks 10/min |
| Cost guard | Partial | Daily global estimate; rubric asks $10/month/user in Redis |
| Health check | Passed | Public `/health` returned `200` |
| Readiness check | Passed | Public `/ready` returned `200` |
| Graceful shutdown | Passed in code | Lifespan plus SIGTERM handling |
| Stateless conversation design | Passed | `/ask` runs are independent |
| Fully distributed counters | Not yet | Rate and budget counters still use process memory |
| Redis | Partial | Compose service/config exists; final counters do not use it |
| Structured logging | Passed | JSON event logs |
| Public cloud deployment | Passed | Railway URL is working |
| No committed `.env.local` | Passed | File is ignored by root `.gitignore` |
| Screenshots | Not yet | Add Railway dashboard and endpoint screenshots |

---

## Verification Commands

```bash
BASE_URL="https://ntdungtest-826c.up.railway.app"

curl -i "$BASE_URL/health"
curl -i "$BASE_URL/ready"
curl -i "$BASE_URL/tools"

# Expected: 401
curl -i -X POST "$BASE_URL/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# Replace with a valid key stored outside Git.
curl -i -X POST "$BASE_URL/ask" \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question":"Reply exactly: DEPLOYMENT_OK"}'
```

Local verification:

```bash
cd 06-lab-complete
python -m unittest discover -s tests -v
python check_production_ready.py
```

Recorded local results:

```text
6 tests passed
23/23 production readiness checks passed
```

---

## Remaining Work Before Submission

1. Add `screenshots/dashboard.png`, `screenshots/running.png`, and
   `screenshots/test.png`.
2. Create `DEPLOYMENT.md` if it is not already present.
3. Set `RATE_LIMIT_PER_MINUTE=10` for exact rubric compliance.
4. Move rate-limit and budget counters to Redis.
5. Change the budget period to `$10/month per user` if strict final-project
   compliance is required.
6. Run and capture the three-instance stateless Docker test.
7. Confirm the repository is public or shared with the instructor.

