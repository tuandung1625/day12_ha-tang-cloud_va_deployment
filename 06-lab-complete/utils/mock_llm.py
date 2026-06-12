"""Offline fallback used when GEMINI_API_KEY is not configured."""
import random


RESPONSES = [
    "Agent is running in mock mode. Configure GEMINI_API_KEY to enable tool use.",
    "This is an offline response. The production API and safety controls are active.",
    "The request was received, but live model tools require GEMINI_API_KEY.",
]


def ask(question: str) -> str:
    if "tool" in question.lower():
        return (
            "Available tools are listed at GET /tools. "
            "Configure GEMINI_API_KEY so the model can choose and call them."
        )
    return random.choice(RESPONSES)
