"""FastAPI agent ready to deploy on Render."""
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from utils.mock_llm import ask


app = FastAPI(title="Agent on Render", version="1.0.0")
START_TIME = time.time()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@app.get("/")
def root():
    return {
        "message": "AI Agent running on Render!",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/ask")
def ask_agent(body: AskRequest):
    if not body.question.strip():
        raise HTTPException(status_code=422, detail="question required")
    return {
        "question": body.question,
        "answer": ask(body.question),
        "platform": "Render",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "platform": "Render",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
