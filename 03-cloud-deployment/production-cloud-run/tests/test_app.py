from app import AskRequest, ask_agent, health, ready


def test_health():
    assert health()["status"] == "ok"


def test_ready():
    assert ready() == {"ready": True}


def test_ask():
    response = ask_agent(AskRequest(question="Cloud deployment la gi?"))
    assert response["platform"] == "Google Cloud Run"
