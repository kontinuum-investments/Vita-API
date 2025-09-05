from dotenv import load_dotenv

load_dotenv()
from main import chronos_app

from fastapi.testclient import TestClient

client = TestClient(chronos_app)


def test_ping() -> None:
    response = client.get("/ping")
    assert response.status_code == 200