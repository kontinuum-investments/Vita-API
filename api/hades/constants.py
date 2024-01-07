from _decimal import Decimal
from enum import Enum

ROUTE__ORGANIZE_MONTHLY_FINANCES: str = "/organize_monthly_finances"
ROUTE__WEBHOOK_WISE__ACCOUNT_UPDATE: str = "/webhook_wise_account_update"
DAILY_FINANCES__MONTHLY_BUDGET: Decimal = Decimal("1000")


class WiseReserveAccount(Enum):
    DAILY_EXPENSES: str = "Daily Expenses (Needs)"
    SALARY: str = "Salary"
