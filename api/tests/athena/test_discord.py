import pytest
from httpx import Response

from api.athena import constants
from api.athena.constants import DiscordTextChannel
from api.athena.models import http
from api.constants import ROUTE__ATHENA
from api.tests import put


class TestDiscord:

    @pytest.mark.asyncio
    async def test_send_message_to_existing_channel(self) -> None:
        message: http.Message = http.Message(text_channel_name=DiscordTextChannel.NOTIFICATION.value, message="Test Message")# type: ignore[attr-defined]
        response: Response = await put(f"{ROUTE__ATHENA}{constants.ROUTE__SEND_MESSAGE}", json=message.model_dump())
        assert response.status_code == 200

    # TODO
    @pytest.mark.skip(reason="Test doesn't work since it doesn't see that the ClientException is already handled")
    @pytest.mark.asyncio
    async def test_send_message_to_non_existent_channel(self) -> None:
        message: http.Message = http.Message(text_channel_name="Non-Existent-Channel", message="Test Message")
        response: Response = await put(f"{ROUTE__ATHENA}{constants.ROUTE__SEND_MESSAGE}", json=message.model_dump())
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_send_message_to_notification_channel(self) -> None:
        message: http.Message = http.Message(message="Test Notification Message")
        response: Response = await put(f"{ROUTE__ATHENA}{constants.ROUTE__SEND_NOTIFICATION_MESSAGE}", json=message.model_dump())
        assert response.status_code == 200
