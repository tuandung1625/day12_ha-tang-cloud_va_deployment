"""Minimal stateless FastAPI service for Google Cloud Run."""
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn


app = FastAPI(title="Agent on Cloud Run", version="1.0.0")
START_TIME = time.time()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@app.get("/")
def root():
    return {
        "message": "AI Agent running on Cloud Run!",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }


@app.post("/ask")
def ask_agent(body: AskRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="question required")
    return {
        "question": question,
        "answer": "Cloud Run da nhan cau hoi. Day la mock response.",
        "platform": "Google Cloud Run",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    return {"ready": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
