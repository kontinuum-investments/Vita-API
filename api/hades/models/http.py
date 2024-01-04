import datetime
from _decimal import Decimal
from typing import List

from sirius.common import DataClass, Currency

import api.hades.common
from api.hades.services import monthly_financial_organisation


class DailyFinances(DataClass):
    monthly_budget: Decimal
    daily_budget: Decimal
    is_over_budget: bool
    amount_under_budget: Decimal | None = None
    amount_over_budget: Decimal | None = None
    date_budget_reached: datetime.date | None = None


class MonthlyFinancePlannedExpense(DataClass):
    description: str
    amount: Decimal
    currency: Currency
    reserve_account_name: str | None = None
    recipient_name: str | None = None
    notification_phone_number: str | None = None

    @staticmethod
    def get_from_planned_expense(planned_expense: api.hades.common.PlannedExpense) -> "MonthlyFinancePlannedExpense":
        return MonthlyFinancePlannedExpense(
            description=planned_expense.description,
            amount=planned_expense.amount,
            currency=planned_expense.reserve_account.currency if planned_expense.reserve_account is not None else planned_expense.recipient.currency,
            reserve_account_name=planned_expense.reserve_account.name if planned_expense.reserve_account is not None else None,
            recipient_name=planned_expense.recipient.account_holder_name if planned_expense.recipient is not None else None,
            notification_phone_number=planned_expense.notification_phone_number
        )


class MonthlyFinances(DataClass):
    salary: Decimal
    needs: Decimal
    wants: Decimal
    needs_planned_expense_list: List[MonthlyFinancePlannedExpense]
    wants_planned_expense_list: List[MonthlyFinancePlannedExpense]
    scheduled_planned_expense_list: List[MonthlyFinancePlannedExpense]
    savings: MonthlyFinancePlannedExpense

    @staticmethod
    def get_from_monthly_finances(monthly_finances: monthly_financial_organisation.MonthlyFinances) -> "MonthlyFinances":
        return MonthlyFinances(
            salary=monthly_finances.salary,
            needs=monthly_finances.needs,
            wants=monthly_finances.wants,
            needs_planned_expense_list=[MonthlyFinancePlannedExpense.get_from_planned_expense(transfer) for transfer in monthly_finances.needs_planned_expense_list],
            wants_planned_expense_list=[MonthlyFinancePlannedExpense.get_from_planned_expense(transfer) for transfer in monthly_finances.wants_planned_expense_list],
            scheduled_planned_expense_list=[MonthlyFinancePlannedExpense.get_from_planned_expense(transfer) for transfer in monthly_finances.scheduled_planned_expense_list],
            savings=MonthlyFinancePlannedExpense.get_from_planned_expense(monthly_finances.savings)
        )
