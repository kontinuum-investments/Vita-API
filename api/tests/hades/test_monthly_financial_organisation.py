import datetime
from decimal import Decimal

import pytest
from sirius.common import Currency
from sirius.http_requests import ServerSideException
from sirius.wise import WiseAccount, WiseAccountType, CashAccount, ReserveAccount

from api import common
from api.constants import ROUTE__HADES
from api.exceptions import ClientException
from api.hades import constants
from api.hades.common import FinancesSettings
from api.hades.services.monthly_financial_organisation import MonthlyFinances
from api.tests import post


@pytest.mark.skip("Requires verification in Wise Sandbox to transfer savings")
@pytest.mark.xfail(raises=ServerSideException)
@pytest.mark.asyncio
async def test_sufficient_funds_in_account() -> None:
    monthly_finances: MonthlyFinances = MonthlyFinances.get_monthly_finances()
    wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
    salary_reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account("Salary", Currency.NZD, True)
    nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD, True)
    await salary_reserve_account._set_balance(monthly_finances.salary)

    await post(f"{ROUTE__HADES}{constants.ROUTE__ORGANIZE_MONTHLY_FINANCES}")

    assert nzd_account.balance == Decimal("0")
    assert wise_account.personal_profile.get_reserve_account("Daily Expenses (Needs)", Currency.NZD).balance == Decimal("1000")
    assert wise_account.personal_profile.get_reserve_account("Daily Expenses (Wants)", Currency.NZD).balance == Decimal("500")


@pytest.mark.xfail(raises=ServerSideException)
@pytest.mark.asyncio
async def test_insufficient_funds_in_account() -> None:
    excel_file_path: str = FinancesSettings.get_monthly_finances_excel_file_path()
    monthly_finances: MonthlyFinances = MonthlyFinances.get_monthly_finances(excel_file_path=excel_file_path)
    wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
    FinancesSettings.get_cash_reserve_amount()
    salary_reserve_account: ReserveAccount = FinancesSettings.get_salary_reserve_account(wise_account, excel_file_path)
    await salary_reserve_account._set_balance(monthly_finances.salary - Decimal("1"))

    with pytest.raises(ClientException):
        await post(f"{ROUTE__HADES}{constants.ROUTE__ORGANIZE_MONTHLY_FINANCES}")
