import asyncio
from asyncio import AbstractEventLoop

import pytest
from httpx import Response
from sirius.iam.microsoft_entra_id import MicrosoftIdentityToken

from api.ares import constants
from api.ares.models import http
from api.ares.models.http import ConnectionInfo
from api.constants import ROUTE__ARES
from api.tests import post, get


@pytest.fixture(scope="session")
def event_loop() -> AbstractEventLoop:
    return asyncio.get_event_loop()


@pytest.mark.skip(reason="Requires Interaction")
@pytest.mark.asyncio
async def test_login() -> None:
    response: Response = await post(f"{ROUTE__ARES}{constants.ROUTE__LOGIN}", json=http.Login(application_name="Test Application").model_dump())
    microsoft_identity_token: MicrosoftIdentityToken = MicrosoftIdentityToken(**response.json())
    assert microsoft_identity_token.access_token is not None


@pytest.mark.asyncio
async def test_get_connection_data() -> None:
    response: Response = await get(f"{ROUTE__ARES}{constants.ROUTE__GET_CONNECTION_INFO}")
    connection_info: ConnectionInfo = ConnectionInfo(**response.json())
    assert connection_info.client_ip is not None
