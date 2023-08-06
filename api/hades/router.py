from typing import Any

from fastapi import APIRouter

from api.common import Discord
from api.constants import ROUTE__HADES
from api.hades import services, constants
from api.hades.models import http

hades_router = APIRouter(prefix=ROUTE__HADES)


@hades_router.post(constants.ROUTE__ORGANIZE_DAILY_FINANCES)
async def organize_daily_finances() -> http.DailyFinances:
    return await services.DailyFinances.do()


@hades_router.post(constants.ROUTE__WEBHOOK)
async def webhook(data: Any) -> None:
    await Discord.notify(f"Webhook data: \n"
                         f"{str(data)}")
