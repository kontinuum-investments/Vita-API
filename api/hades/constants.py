from enum import Enum

from _decimal import Decimal

ROUTE__ORGANIZE_DAILY_FINANCES: str = "/organize_daily_finances"
ROUTE__FINANCES_FOR_NEXT_MONTH: str = "/monthly_finances"
ROUTE__ORGANIZE_MONTHLY_FINANCES: str = "/organize_monthly_finances"
ROUTE__ORGANIZE_MONTHLY_FINANCES_WHEN_SALARY_RECEIVED: str = "/organize_monthly_finances_when_salary_received"
ROUTE__ORGANIZE_RENT: str = "/organize_rent"
ROUTE__WEBHOOK_WISE__PRIMARY_ACCOUNT_UPDATE: str = "/webhook_primary_wise_account_update"
ROUTE__WEBHOOK_WISE__SECONDARY_ACCOUNT_UPDATE: str = "/webhook_secondary_wise_account_update"
DAILY_FINANCES__MONTHLY_BUDGET: Decimal = Decimal("1000")


class WiseReserveAccount(Enum):
    DAILY_EXPENSES: str = "Daily Expenses (Needs)"
    SALARY: str = "Salary"
