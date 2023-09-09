from typing import Annotated

from fastapi import APIRouter, Depends
from sirius.iam.microsoft_entra_id import MicrosoftIdentity
from starlette.requests import Request

import api.hades.services.organize_daily_finances
from api.ares.router import get_microsoft_identity
from api.athena.services.discord import Discord
from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.models import http

hades_router = APIRouter(prefix=ROUTE__HADES)


@hades_router.post(constants.ROUTE__ORGANIZE_DAILY_FINANCES)
async def organize_daily_finances(microsoft_identity: Annotated[MicrosoftIdentity, Depends(get_microsoft_identity)]) -> http.DailyFinances:
    return await api.hades.services.organize_daily_finances.DailyFinances.do()


@hades_router.post(constants.ROUTE__WEBHOOK_WISE__ACCOUNT_UPDATE)
async def webhook_account_update(request: Request) -> None:
    await Discord.notify((await request.body()).decode("utf-8"))
    # await AccountUpdate.handle_balance_update(wise_web_hook)
