from dotenv import load_dotenv

load_dotenv()

from ai_service_main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_ping() -> None:
    response = client.get("/ping")
    assert response.status_code == 200
