from enum import Enum

from _decimal import Decimal

ROUTE__ORGANIZE_DAILY_FINANCES: str = "/organize_daily_finances"
ROUTE__WEBHOOK_WISE__ACCOUNT_UPDATE: str = "/webhook_wise_account_update"
DAILY_FINANCES__MONTHLY_BUDGET: Decimal = Decimal("1000")


class WiseReserveAccount(Enum):
    MONTHLY_EXPENSES: str = "Monthly Expenses"
