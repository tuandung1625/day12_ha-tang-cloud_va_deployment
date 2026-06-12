"""Small mock LLM so the deployment example needs no paid API key."""
import random
import time


RESPONSES = [
    "Agent tren Render dang hoat dong tot.",
    "Day la cau tra loi mo phong. Ban co the thay bang LLM that sau.",
    "Deployment da nhan duoc cau hoi cua ban.",
]


def ask(question: str) -> str:
    time.sleep(0.1)
    if "deploy" in question.lower():
        return "Deployment la qua trinh dua ung dung len moi truong de nguoi dung truy cap."
    return random.choice(RESPONSES)
