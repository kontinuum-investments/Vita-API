import calendar
import datetime
from datetime import date

import pytest
from _decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from httpx import Response
from sirius import common
from sirius.wise import ReserveAccount, WiseAccountType, WiseAccount, CashAccount

from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.constants import WiseReserveAccount
from api.hades.models import http
from api.tests import post


class TestOrganizeDailyFinances:

    @staticmethod
    def _get_daily_budget() -> Decimal:
        number_of_days_in_month: Decimal = Decimal(calendar.monthrange(datetime.datetime.now().year, datetime.datetime.now().month)[1])
        return (constants.DAILY_FINANCES__MONTHLY_BUDGET / number_of_days_in_month) \
            .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def _get_expected_balance_at_start_of_day() -> Decimal:
        return (TestOrganizeDailyFinances._get_expected_balance_at_end_of_day() + TestOrganizeDailyFinances._get_daily_budget()) \
            .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def _get_expected_balance_at_end_of_day() -> Decimal:
        return constants.DAILY_FINANCES__MONTHLY_BUDGET - (TestOrganizeDailyFinances._get_daily_budget() * Decimal(datetime.datetime.now().day)) \
            .quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def _get_day_budget_is_reached(amount_over_budget: Decimal) -> date:
        number_of_days_till_budget_reached: int = int((amount_over_budget / TestOrganizeDailyFinances._get_daily_budget()).quantize(Decimal('1'), rounding=ROUND_CEILING))
        return (datetime.datetime.now() + datetime.timedelta(days=number_of_days_till_budget_reached)).date()

    @pytest.mark.asyncio
    async def test_in_budget(self) -> None:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(common.Currency.NZD, True)
        reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(WiseReserveAccount.DAILY_EXPENSES.value, common.Currency.NZD, True)
        await nzd_account._set_balance(Decimal("0"))
        await reserve_account._set_balance(TestOrganizeDailyFinances._get_expected_balance_at_start_of_day())

        response: Response = await post(f"{ROUTE__HADES}{constants.ROUTE__ORGANIZE_DAILY_FINANCES}")

        actual_response: http.DailyFinances = http.DailyFinances(**response.json())
        expected_response: http.DailyFinances = http.DailyFinances(
            monthly_budget=constants.DAILY_FINANCES__MONTHLY_BUDGET,
            daily_budget=TestOrganizeDailyFinances._get_daily_budget(),
            amount_under_budget=Decimal("0"),
            is_over_budget=False
        )

        assert actual_response == expected_response
        wise_account._initialize()
        assert nzd_account.balance == expected_response.daily_budget
        assert reserve_account.balance == TestOrganizeDailyFinances._get_expected_balance_at_end_of_day()

    @pytest.mark.asyncio
    async def test_under_budget(self) -> None:
        amount_under_budget: Decimal = Decimal("100")
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(common.Currency.NZD, True)
        reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(WiseReserveAccount.DAILY_EXPENSES.value, common.Currency.NZD, True)
        await nzd_account._set_balance(amount_under_budget)
        await reserve_account._set_balance(TestOrganizeDailyFinances._get_expected_balance_at_start_of_day())

        response: Response = await post(f"{ROUTE__HADES}{constants.ROUTE__ORGANIZE_DAILY_FINANCES}")

        actual_response: http.DailyFinances = http.DailyFinances(**response.json())
        expected_response: http.DailyFinances = http.DailyFinances(
            monthly_budget=constants.DAILY_FINANCES__MONTHLY_BUDGET,
            daily_budget=TestOrganizeDailyFinances._get_daily_budget(),
            amount_under_budget=amount_under_budget,
            is_over_budget=False
        )
        assert actual_response == expected_response
        wise_account._initialize()
        assert nzd_account.balance == amount_under_budget + expected_response.daily_budget
        assert reserve_account.balance == TestOrganizeDailyFinances._get_expected_balance_at_end_of_day()

    @pytest.mark.asyncio
    async def test_over_budget(self) -> None:
        amount_over_budget: Decimal = Decimal("100")
        reserve_account_balance: Decimal = TestOrganizeDailyFinances._get_expected_balance_at_start_of_day() - amount_over_budget
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(common.Currency.NZD, True)
        reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(WiseReserveAccount.DAILY_EXPENSES.value, common.Currency.NZD, True)
        await nzd_account._set_balance(Decimal("0"))
        await reserve_account._set_balance(reserve_account_balance)

        response: Response = await post(f"{ROUTE__HADES}{constants.ROUTE__ORGANIZE_DAILY_FINANCES}")

        actual_response: http.DailyFinances = http.DailyFinances(**response.json())
        expected_response: http.DailyFinances = http.DailyFinances(
            monthly_budget=constants.DAILY_FINANCES__MONTHLY_BUDGET,
            daily_budget=TestOrganizeDailyFinances._get_daily_budget(),
            amount_over_budget=amount_over_budget,
            date_budget_reached=TestOrganizeDailyFinances._get_day_budget_is_reached(amount_over_budget),
            is_over_budget=True
        )
        assert actual_response == expected_response
        wise_account._initialize()
        assert nzd_account.balance == Decimal("0")
        assert reserve_account.balance == reserve_account_balance

    @pytest.mark.asyncio
    async def test_over_budget_but_enough_in_cash_account(self) -> None:
        amount_over_budget: Decimal = Decimal("10")
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(common.Currency.NZD, True)
        reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(WiseReserveAccount.DAILY_EXPENSES.value, common.Currency.NZD, True)
        await nzd_account._set_balance(amount_over_budget)
        await reserve_account._set_balance(TestOrganizeDailyFinances._get_expected_balance_at_start_of_day() - amount_over_budget)

        response: Response = await post(f"{ROUTE__HADES}{constants.ROUTE__ORGANIZE_DAILY_FINANCES}")

        actual_response: http.DailyFinances = http.DailyFinances(**response.json())
        expected_response: http.DailyFinances = http.DailyFinances(
            monthly_budget=constants.DAILY_FINANCES__MONTHLY_BUDGET,
            daily_budget=TestOrganizeDailyFinances._get_daily_budget(),
            amount_under_budget=Decimal("0"),
            is_over_budget=False
        )
        assert actual_response == expected_response
        wise_account._initialize()
        assert nzd_account.balance == TestOrganizeDailyFinances._get_daily_budget()
        assert reserve_account.balance == TestOrganizeDailyFinances._get_expected_balance_at_end_of_day()

    @pytest.mark.asyncio
    async def test_over_budget_but_not_enough_in_cash_account(self) -> None:
        cash_account_balance: Decimal = Decimal("90")
        reserve_account_amount_over_budget: Decimal = Decimal("100")
        amount_over_budget: Decimal = reserve_account_amount_over_budget - cash_account_balance
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(common.Currency.NZD, True)
        reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(WiseReserveAccount.DAILY_EXPENSES.value, common.Currency.NZD, True)
        await nzd_account._set_balance(cash_account_balance)
        await reserve_account._set_balance(TestOrganizeDailyFinances._get_expected_balance_at_start_of_day() - reserve_account_amount_over_budget)

        response: Response = await post(f"{ROUTE__HADES}{constants.ROUTE__ORGANIZE_DAILY_FINANCES}")

        actual_response: http.DailyFinances = http.DailyFinances(**response.json())
        expected_response: http.DailyFinances = http.DailyFinances(
            monthly_budget=constants.DAILY_FINANCES__MONTHLY_BUDGET,
            daily_budget=TestOrganizeDailyFinances._get_daily_budget(),
            amount_over_budget=amount_over_budget,
            date_budget_reached=TestOrganizeDailyFinances._get_day_budget_is_reached(amount_over_budget),
            is_over_budget=True
        )
        assert actual_response == expected_response
        wise_account._initialize()
        assert nzd_account.balance == Decimal("0")
        assert reserve_account.balance == TestOrganizeDailyFinances._get_expected_balance_at_start_of_day() - reserve_account_amount_over_budget + cash_account_balance
