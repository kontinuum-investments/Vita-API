from dotenv import load_dotenv

load_dotenv()
from main import apollo_app

from io import BytesIO

from fastapi.testclient import TestClient

client = TestClient(apollo_app)


def test_ping() -> None:
    response = client.get("/ping")
    assert response.status_code == 200


def test_yolov8n_endpoint() -> None:
    with open("apollo/test/person.jpg", "rb") as f:
        image_bytes = BytesIO(f.read())

    response = client.post("/media/object_detection", files={"image": ("person.jpg", image_bytes.getvalue(), "image/jpeg")})
    assert "person" in [data["description"] for data in response.json()]
