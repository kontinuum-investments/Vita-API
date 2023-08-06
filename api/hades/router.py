from fastapi import APIRouter

import api.hades.services.organize_daily_finances
from api.common import Discord
from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.models import http
from api.hades.services.wise_webhook import AccountUpdate

hades_router = APIRouter(prefix=ROUTE__HADES)


@hades_router.post(constants.ROUTE__ORGANIZE_DAILY_FINANCES)
async def organize_daily_finances() -> http.DailyFinances:
    return await api.hades.services.organize_daily_finances.DailyFinances.do()


@hades_router.post(constants.ROUTE__WEBHOOK_WISE__ACCOUNT_UPDATE)
async def webhook(wise_web_hook: http.WiseWebHook) -> None:
    await AccountUpdate.handle_balance_update(wise_web_hook)
