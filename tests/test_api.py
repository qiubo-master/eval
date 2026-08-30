from fastapi.testclient import TestClient

from llm_eval_system.api import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}

