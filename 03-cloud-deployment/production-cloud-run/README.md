# Deploy FastAPI len Google Cloud Run

Thu muc nay chay doc lap va dung mock response, nen khong can API key LLM.

## 1. Chay local

```bash
cd 03-cloud-deployment/production-cloud-run
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q
uvicorn app:app --host 0.0.0.0 --port 8080
```

Mo terminal khac de test:

```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Cloud deployment la gi?"}'
```

## 2. Setup Google Cloud mot lan

Can co billing account va cai Google Cloud CLI (`gcloud`).

```bash
gcloud auth login
gcloud projects create YOUR_PROJECT_ID
gcloud config set project YOUR_PROJECT_ID
gcloud billing projects link YOUR_PROJECT_ID \
  --billing-account=YOUR_BILLING_ACCOUNT_ID

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

gcloud artifacts repositories create cloud-run-source-deploy \
  --repository-format=docker \
  --location=asia-southeast1 \
  --description="Cloud Run images"
```

Neu project da ton tai, bo qua lenh `gcloud projects create`. Xem billing account:

```bash
gcloud billing accounts list
```

## 3. Build va deploy

Chay trong chinh thu muc `production-cloud-run`:

```bash
gcloud builds submit \
  --config cloudbuild.yaml \
  --region=asia-southeast1 \
  .
```

Lay URL va test:

```bash
SERVICE_URL=$(gcloud run services describe ai-agent \
  --region=asia-southeast1 \
  --format='value(status.url)')

curl "$SERVICE_URL/health"
curl -X POST "$SERVICE_URL/ask" \
  -H 'Content-Type: application/json' \
  -d '{"question":"Cloud Run la gi?"}'
```

## 4. Deploy bang service.yaml (tuy chon)

Thay `PROJECT_ID` trong `service.yaml`, sau do:

```bash
gcloud run services replace service.yaml --region=asia-southeast1
```

`cloudbuild.yaml` la cach de dung cho luong build/deploy day du. `service.yaml`
phu hop khi muon quan ly rieng cau hinh service theo Infrastructure as Code.
