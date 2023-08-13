from typing import Annotated

from fastapi import APIRouter, Depends
from sirius.iam.microsoft_entra_id import MicrosoftIdentity

from api.ares.router import get_microsoft_identity
from api.athena import constants
from api.athena.constants import DiscordTextChannel
from api.athena.models import http
from api.athena.services.discord import Discord
from api.constants import ROUTE__ATHENA
from api.exceptions import ClientException

athena_router = APIRouter(prefix=ROUTE__ATHENA)


@athena_router.put(constants.ROUTE__SEND_MESSAGE)
async def send_message(microsoft_identity: Annotated[MicrosoftIdentity, Depends(get_microsoft_identity)], message: http.Message) -> None:
    try:
        discord_text_channel: DiscordTextChannel = DiscordTextChannel(message.text_channel_name.lower())
    except ValueError:
        raise ClientException(f"Unknown Discord Text Channel: {message.text_channel_name}")

    await Discord.send_message(discord_text_channel, message.message)
