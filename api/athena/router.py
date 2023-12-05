import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from sirius.iam import Identity
from starlette.requests import Request
from starlette.responses import JSONResponse

from api.ares.router import get_identity
from api.athena import constants
from api.athena.constants import DiscordTextChannel
from api.athena.models import http
from api.athena.services.discord import Discord
from api.constants import ROUTE__ATHENA
from api.exceptions import ClientException

athena_router = APIRouter(prefix=ROUTE__ATHENA)


@athena_router.put(constants.ROUTE__SEND_MESSAGE)
async def send_message(identity: Annotated[Identity, Depends(get_identity)], message: http.Message) -> None:
    try:
        discord_text_channel: DiscordTextChannel = DiscordTextChannel(message.text_channel_name.lower())
    except ValueError:
        raise ClientException(f"Unknown Discord Text Channel: {message.text_channel_name}")

    await Discord.send_message(discord_text_channel, message.message)


@athena_router.put(constants.ROUTE__SEND_NOTIFICATION_MESSAGE)
async def send_notification_message(identity: Annotated[Identity, Depends(get_identity)], message: http.Message) -> None:
    await Discord.notify(message.message)


@athena_router.post(constants.ROUTE__DISCORD__RECEIVE_MESSAGE)
async def discord_receive_message(request: Request) -> JSONResponse:
    asyncio.ensure_future(test_webhook(request))
    return await Discord.handle_receive_message(request)


@athena_router.post(constants.ROUTE__TEST_WEBHOOK)
async def test_webhook(request: Request) -> None:
    message: str = f"**POST Request Received**\n\n" \
                   f"*Body*: {(await request.body()).decode('utf-8')}\n\n" \
                   f"*Headers*: {str(request.headers)}\n"
    await Discord.notify(message)
