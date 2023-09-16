from typing import Annotated

from fastapi import APIRouter, Depends
from sirius.iam.microsoft_entra_id import MicrosoftIdentity
from sirius.wise import WiseAccountType
from starlette.requests import Request

import api.hades.services.organize_daily_finances
from api.ares.router import get_microsoft_identity
from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.models import http
from api.hades.services.organize_monthly_finances import Summary
from api.hades.services.wise_webhook import AccountUpdate

hades_router = APIRouter(prefix=ROUTE__HADES)


@hades_router.post(constants.ROUTE__ORGANIZE_DAILY_FINANCES)
async def organize_daily_finances(microsoft_identity: Annotated[MicrosoftIdentity, Depends(get_microsoft_identity)]) -> http.DailyFinances:
    return await api.hades.services.organize_daily_finances.DailyFinances.do()


@hades_router.post(constants.ROUTE__ORGANIZE_MONTHLY_FINANCES_FOR_NEXT_MONTH)
async def organize_monthly_finances_for_next_month(microsoft_identity: Annotated[MicrosoftIdentity, Depends(get_microsoft_identity)]) -> Summary:
    return await api.hades.services.organize_monthly_finances.MonthlyFinances.organize_finances_for_next_month()


@hades_router.post(constants.ROUTE__ORGANIZE_MONTHLY_FINANCES_WHEN_SALARY_RECEIVED)
async def organize_finances_when_salary_received(microsoft_identity: Annotated[MicrosoftIdentity, Depends(get_microsoft_identity)]) -> Summary:
    return await api.hades.services.organize_monthly_finances.MonthlyFinances.organize_finances_when_salary_received()


@hades_router.post(constants.ROUTE__WEBHOOK_WISE__PRIMARY_ACCOUNT_UPDATE)
async def webhook_primary_account_update(request: Request) -> None:
    await AccountUpdate.handle_account_update(request, WiseAccountType.PRIMARY)


@hades_router.post(constants.ROUTE__WEBHOOK_WISE__SECONDARY_ACCOUNT_UPDATE)
async def webhook_secondary_account_update(request: Request) -> None:
    await AccountUpdate.handle_account_update(request, WiseAccountType.SECONDARY)
