import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from sirius.iam import Identity
from starlette.requests import Request

from api.ares.router import get_identity
from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.models.http import MonthlyFinances
from api.hades.services import monthly_financial_organisation
from api.hades.services.transaction_organisation import AccountUpdate

hades_router = APIRouter(prefix=ROUTE__HADES)


@hades_router.get(constants.ROUTE__ORGANIZE_MONTHLY_FINANCES)
async def get_monthly_finances(microsoft_identity: Annotated[Identity, Depends(get_identity)]) -> MonthlyFinances:
    monthly_finances: monthly_financial_organisation.MonthlyFinances = monthly_financial_organisation.MonthlyFinances.get_monthly_finances()
    return MonthlyFinances.get_from_monthly_finances(monthly_finances)


@hades_router.post(constants.ROUTE__ORGANIZE_MONTHLY_FINANCES)
async def organize_monthly_finances(microsoft_identity: Annotated[Identity, Depends(get_identity)]) -> MonthlyFinances:
    monthly_finances: monthly_financial_organisation.MonthlyFinances = await monthly_financial_organisation.MonthlyFinances.do()
    return MonthlyFinances.get_from_monthly_finances(monthly_finances)


@hades_router.post(constants.ROUTE__WEBHOOK_WISE__ACCOUNT_UPDATE)
async def webhook_account_update(request: Request) -> None:
    await AccountUpdate.handle_account_update(request)
