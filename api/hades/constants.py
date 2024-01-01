from _decimal import Decimal
from enum import Enum

ROUTE__ORGANIZE_DAILY_FINANCES: str = "/organize_daily_finances"
ROUTE__MONTHLY_FINANCES: str = "/monthly_finances"
ROUTE__ORGANIZE_MONTHLY_FINANCES: str = "/organize_monthly_finances"
ROUTE__ORGANIZE_RENT: str = "/organize_rent"
ROUTE__WEBHOOK_WISE__PRIMARY_ACCOUNT_UPDATE: str = "/webhook_primary_wise_account_update"
ROUTE__WEBHOOK_WISE__SECONDARY_ACCOUNT_UPDATE: str = "/webhook_secondary_wise_account_update"
DAILY_FINANCES__MONTHLY_BUDGET: Decimal = Decimal("1000")


class WiseReserveAccount(Enum):
    DAILY_EXPENSES: str = "Daily Expenses (Needs)"
    SALARY: str = "Salary"
