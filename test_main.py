from dotenv import load_dotenv

load_dotenv()

from fastapi.testclient import TestClient

from main import app
from tools.discord import SendMessage

client = TestClient(app)


def test_send_discord_message() -> None:
    response = client.post("/discord/send_message/", json=SendMessage(message="Hello World").model_dump())
    assert response.status_code == 200


def test_get_ibkr_account_summary() -> None:
    response = client.get("/ibkr/account_summary/")
    assert response.status_code == 200


def test_get_latest_transactions() -> None:
    response = client.get("/wise/latest_transactions/")
    assert response.status_code == 200


def test_get_account_summary() -> None:
    response = client.get("/wise/account_summary/")
    assert response.status_code == 200
