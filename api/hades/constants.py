from enum import Enum

from _decimal import Decimal

ROUTE__ORGANIZE_DAILY_FINANCES: str = "/organize_daily_finances"
DAILY_FINANCES__MONTHLY_BUDGET: Decimal = Decimal("1000")


class WiseReserveAccount(Enum):
    MONTHLY_EXPENSES: str = "Monthly Expenses"
