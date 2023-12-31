import calendar
import datetime
from _decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING

from sirius import common
from sirius.wise import WiseAccount, CashAccount, ReserveAccount, WiseAccountType

from api.athena.services.discord import Discord
from api.hades import constants
from api.hades.constants import WiseReserveAccount
from api.hades.models import http


class DailyFinances:
    message_header: str = f"**Daily Expense Notification:**\n"
    wise_account: WiseAccount
    nzd_account: CashAccount
    reserve_account: ReserveAccount
    monthly_budget: Decimal = constants.DAILY_FINANCES__MONTHLY_BUDGET
    daily_budget: Decimal
    expected_balance_at_start_of_day: Decimal
    expected_balance_at_end_of_day: Decimal
    amount_under_budget: Decimal
    amount_over_budget: Decimal
    number_of_days_till_budget_reached: int | None
    date_budget_reached: datetime.date | None
    is_over_budget: bool

    def _initialize(self) -> None:
        self._set_daily_budget()
        self._set_expected_balance_at_end_of_day()
        self.expected_balance_at_start_of_day = self.expected_balance_at_end_of_day + self.daily_budget
        self.amount_under_budget = (self.nzd_account.balance + self.reserve_account.balance) - self.expected_balance_at_start_of_day
        self.is_over_budget = self.amount_under_budget < Decimal("0")
        self._set_date_budget_reached()

    def _set_daily_budget(self) -> None:
        monthly_budget: Decimal = constants.DAILY_FINANCES__MONTHLY_BUDGET
        number_of_days_in_month: Decimal = Decimal(calendar.monthrange(datetime.datetime.now().year, datetime.datetime.now().month)[1])
        self.daily_budget = (monthly_budget / number_of_days_in_month).quantize(Decimal("0.01"), ROUND_HALF_UP)

    def _set_expected_balance_at_end_of_day(self) -> None:
        monthly_budget: Decimal = constants.DAILY_FINANCES__MONTHLY_BUDGET
        daily_budget: Decimal = self.daily_budget
        expected_balance_at_end_of_day: Decimal = (monthly_budget - (Decimal(datetime.datetime.now().day) * daily_budget)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        self.expected_balance_at_end_of_day = max(expected_balance_at_end_of_day, Decimal(0))

    def _set_date_budget_reached(self) -> None:
        if not self.is_over_budget:
            self.number_of_days_till_budget_reached = None
            self.date_budget_reached = None
            return

        self.amount_over_budget = self.amount_under_budget * Decimal("-1")
        self.number_of_days_till_budget_reached = int((self.amount_over_budget / self.daily_budget).quantize(Decimal('1'), rounding=ROUND_CEILING))
        self.date_budget_reached = (datetime.datetime.now() + datetime.timedelta(days=self.number_of_days_till_budget_reached)).date()

    @classmethod
    async def do(cls) -> http.DailyFinances:
        daily_finances: DailyFinances = DailyFinances()
        daily_finances.wise_account = WiseAccount.get(WiseAccountType.PRIMARY)
        daily_finances.nzd_account = daily_finances.wise_account.personal_profile.get_cash_account(common.Currency.NZD)
        daily_finances.reserve_account = daily_finances.wise_account.personal_profile.get_reserve_account(WiseReserveAccount.DAILY_EXPENSES.value, common.Currency.NZD, True)
        daily_finances.monthly_budget = constants.DAILY_FINANCES__MONTHLY_BUDGET
        daily_finances._initialize()

        return await DailyFinances._over_budget(daily_finances) if daily_finances.is_over_budget else await DailyFinances._under_budget(daily_finances)

    @classmethod
    async def _under_budget(cls, daily_finances: "DailyFinances") -> http.DailyFinances:
        if daily_finances.reserve_account.balance >= daily_finances.expected_balance_at_end_of_day:
            await daily_finances.reserve_account.transfer(daily_finances.nzd_account, daily_finances.reserve_account.balance - daily_finances.expected_balance_at_end_of_day)
        else:
            await daily_finances.nzd_account.transfer(daily_finances.reserve_account, daily_finances.expected_balance_at_end_of_day - daily_finances.reserve_account.balance)

        await Discord.notify(f"{cls.message_header}"
                             f"*Amount under budget*: {daily_finances.nzd_account.currency.value} {common.get_decimal_str(daily_finances.amount_under_budget)}")

        return http.DailyFinances(
            monthly_budget=daily_finances.monthly_budget,
            daily_budget=daily_finances.daily_budget,
            amount_under_budget=daily_finances.amount_under_budget,
            is_over_budget=daily_finances.is_over_budget
        )

    @classmethod
    async def _over_budget(cls, daily_finances: "DailyFinances") -> http.DailyFinances:
        if daily_finances.nzd_account.balance > Decimal("0"):
            await daily_finances.nzd_account.transfer(daily_finances.reserve_account, daily_finances.nzd_account.balance)

        await Discord.notify(f"{cls.message_header}"
                             f"*Amount over budget*: {daily_finances.nzd_account.currency.value} {common.get_decimal_str(daily_finances.amount_over_budget)}\n"
                             f"*Date budget is reached*: {daily_finances.date_budget_reached.strftime('%Y-%m-%d')} ({daily_finances.number_of_days_till_budget_reached} days)")

        return http.DailyFinances(
            monthly_budget=daily_finances.monthly_budget,
            daily_budget=daily_finances.daily_budget,
            amount_over_budget=daily_finances.amount_over_budget,
            date_budget_reached=daily_finances.date_budget_reached,
            is_over_budget=daily_finances.is_over_budget
        )
