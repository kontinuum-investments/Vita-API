from dotenv import load_dotenv

load_dotenv()
from main import ai_service_app

from io import BytesIO

from fastapi.testclient import TestClient

client = TestClient(ai_service_app)


def test_ping() -> None:
    response = client.get("/ping")
    assert response.status_code == 200


def test_yolov8n_endpoint() -> None:
    with open("ai_service/test/person.jpg", "rb") as f:
        image_bytes = BytesIO(f.read())

    response = client.post("/media/yolov8n", files={"image": ("person.jpg", image_bytes.getvalue(), "image/jpeg")})
    assert "person" in response.json()
