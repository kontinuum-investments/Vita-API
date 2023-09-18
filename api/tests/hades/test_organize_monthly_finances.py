import datetime

import pytest
from _decimal import Decimal
from sirius.common import Currency
from sirius.wise import WiseAccount, WiseAccountType, CashAccount

from api.exceptions import ClientException
from api.hades.services.organize_monthly_finances import MonthlyFinances, Summary, WiseReserveAccount


# Note: These tests aren't comprehensive since it's not possible to determine foreign exchange rates for inter-currency transfers and it is not possible to detect which transfers have been sent
class TestOrganizeMonthlyFinances:
    month: datetime.date = datetime.datetime.strptime("2023-10-01", "%Y-%m-%d").date()

    @pytest.mark.asyncio
    async def test_organize_finances_when_wrong_month_in_excel_file(self) -> None:
        await WiseAccount.get(WiseAccountType.PRIMARY).personal_profile.get_cash_account(Currency.NZD)._set_balance(Decimal("10"))
        with pytest.raises(ClientException):
            await MonthlyFinances.organize_finances_when_salary_received(datetime.datetime.strptime("2020-01-01", "%Y-%m-%d").date())

    @pytest.mark.asyncio
    async def test_organize_finances_when_salary_received_with_no_salary(self) -> None:
        await WiseAccount.get(WiseAccountType.PRIMARY).personal_profile.get_cash_account(Currency.NZD)._set_balance(Decimal("10"))
        with pytest.raises(ClientException):
            await MonthlyFinances.organize_finances_when_salary_received(self.month)

    @pytest.mark.asyncio
    async def test_organize_finances_when_salary_received(self) -> None:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        await nzd_account._set_balance(Decimal("7303.67") + Decimal("10"))

        summary: Summary = await MonthlyFinances.organize_finances_when_salary_received(self.month)
        assert summary is not None

        wise_account._initialize()
        wise_account.personal_profile._complete_all_transfers()
        assert wise_account.personal_profile.get_reserve_account(WiseReserveAccount.SALARY.value, Currency.NZD).balance == Decimal("3790.66")

    @pytest.mark.asyncio
    async def test_organize_finances_for_start_of_month(self) -> None:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        await wise_account.personal_profile.get_reserve_account(WiseReserveAccount.SALARY.value, Currency.NZD, True)._set_balance(Decimal("3790.66"))
        await nzd_account._set_balance(Decimal("10"))

        summary: Summary = await MonthlyFinances.organize_finances_for_at_start_of_month(self.month)
        assert summary is not None

        wise_account._initialize()
        wise_account.personal_profile._complete_all_transfers()
        for key, value in {
            "Daily Expenses (Needs)": Decimal("1000"),
            "Vehicle Maintenance (Needs)": Decimal("50"),
            "Utilities (Needs)": Decimal("150"),
            "Daily Expenses (Wants)": Decimal("500"),
        }.items():
            assert wise_account.personal_profile.get_reserve_account(key, Currency.NZD).balance == value

    @pytest.mark.asyncio
    async def test_organize_finances_for_start_of_month_insufficient_balance(self) -> None:
        await WiseAccount.get(WiseAccountType.PRIMARY).personal_profile.get_reserve_account(WiseReserveAccount.SALARY.value, Currency.NZD, True)._set_balance(Decimal("3780.66"))
        with pytest.raises(ClientException):
            await MonthlyFinances.organize_finances_for_at_start_of_month(self.month)
