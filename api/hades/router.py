import asyncio
import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sirius.iam import Identity
from starlette.requests import Request

import api.hades.services.organize_daily_finances
from api import common
from api.ares.router import get_identity
from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.models import http
from api.hades.models.http import MonthlyFinances
from api.hades.services import monthly_financial_organisation
from api.hades.services.organize_rent import OrganizeRent
from api.hades.services.transaction_organisation import AccountUpdate

hades_router = APIRouter(prefix=ROUTE__HADES)


@hades_router.post(constants.ROUTE__ORGANIZE_DAILY_FINANCES)
async def organize_daily_finances(microsoft_identity: Annotated[Identity, Depends(get_identity)]) -> http.DailyFinances:
    return await api.hades.services.organize_daily_finances.DailyFinances.do()


@hades_router.get(constants.ROUTE__ORGANIZE_MONTHLY_FINANCES)
async def get_monthly_finances(microsoft_identity: Annotated[Identity, Depends(get_identity)], month_string: str | None = None) -> MonthlyFinances:
    month: datetime.date = common.get_first_date_of_next_month(datetime.date.today()) if month_string is None else datetime.datetime.strptime(f"{month_string}-01", "%Y-%m-%d").date()
    monthly_finances: monthly_financial_organisation.MonthlyFinances = monthly_financial_organisation.MonthlyFinances.get_monthly_finances(month)
    return MonthlyFinances.get_from_monthly_finances(monthly_finances)


@hades_router.post(constants.ROUTE__ORGANIZE_MONTHLY_FINANCES)
async def organize_monthly_finances(microsoft_identity: Annotated[Identity, Depends(get_identity)], month_string: str | None = None) -> MonthlyFinances:
    month: datetime.date = common.get_first_date_of_next_month(datetime.date.today()) if month_string is None else datetime.datetime.strptime(f"{month_string}-01", "%Y-%m-%d").date()
    monthly_finances: monthly_financial_organisation.MonthlyFinances = await monthly_financial_organisation.MonthlyFinances.do(month)
    return MonthlyFinances.get_from_monthly_finances(monthly_finances)


@hades_router.post(constants.ROUTE__ORGANIZE_RENT)
async def organize_rent(microsoft_identity: Annotated[Identity, Depends(get_identity)]) -> OrganizeRent:
    return await api.hades.services.organize_rent.OrganizeRent.do()


@hades_router.post(constants.ROUTE__WEBHOOK_WISE__ACCOUNT_UPDATE)
async def webhook_account_update(request: Request) -> None:
    await AccountUpdate.handle_account_update(request)
