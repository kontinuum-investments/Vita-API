from typing import Annotated

from fastapi import APIRouter, Depends
from sirius.iam.microsoft_entra_id import MicrosoftIdentity
from starlette.requests import Request

import api.hades.services.organize_daily_finances
from api.ares.router import get_microsoft_identity
from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.models import http
from api.hades.services.wise_webhook import AccountUpdate

hades_router = APIRouter(prefix=ROUTE__HADES)


@hades_router.post(constants.ROUTE__ORGANIZE_DAILY_FINANCES)
async def organize_daily_finances(microsoft_identity: Annotated[MicrosoftIdentity, Depends(get_microsoft_identity)]) -> http.DailyFinances:
    return await api.hades.services.organize_daily_finances.DailyFinances.do()


@hades_router.post(constants.ROUTE__WEBHOOK_WISE__PRIMARY_ACCOUNT_UPDATE)
async def webhook_primary_account_update(request: Request) -> None:
    try:
        await AccountUpdate.primary_account_update(await request.json())
    except Exception as e:
        await Discord.send_message(DiscordTextChannel.WISE, f"**Unknown Wise Webhook Update (Primary)**\n"
                                                            f"{(await request.body()).decode('utf-8')}")


@hades_router.post(constants.ROUTE__WEBHOOK_WISE__SECONDARY_ACCOUNT_UPDATE)
async def webhook_secondary_account_update(request: Request) -> None:
    try:
        await AccountUpdate.secondary_account_update(await request.json())
    except Exception as e:
        await Discord.send_message(DiscordTextChannel.WISE, f"**Unknown Wise Webhook Update (Secondary)**\n"
                                                            f"{(await request.body()).decode('utf-8')}")
