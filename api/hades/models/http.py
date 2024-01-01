import datetime
from _decimal import Decimal
from typing import List

from sirius.common import DataClass

from api.hades.services import monthly_financial_organisation


class DailyFinances(DataClass):
    monthly_budget: Decimal
    daily_budget: Decimal
    is_over_budget: bool
    amount_under_budget: Decimal | None = None
    amount_over_budget: Decimal | None = None
    date_budget_reached: datetime.date | None = None


class MonthlyFinanceTransfer(DataClass):
    description: str
    amount: Decimal
    reserve_account_name: str | None = None
    recipient_name: str | None = None
    notification_phone_number: str | None = None

    @staticmethod
    def get_from_transfer(transfer: monthly_financial_organisation.Transfer) -> "MonthlyFinanceTransfer":
        return MonthlyFinanceTransfer(
            description=transfer.description,
            amount=transfer.amount,
            reserve_account_name=transfer.reserve_account.name if transfer.reserve_account is not None else None,
            recipient_name=transfer.recipient.account_holder_name if transfer.recipient is not None else None,
            notification_phone_number=transfer.notification_phone_number
        )


class MonthlyFinances(DataClass):
    salary: Decimal
    needs: Decimal
    wants: Decimal
    needs_transfer_list: List[MonthlyFinanceTransfer]
    wants_transfer_list: List[MonthlyFinanceTransfer]
    scheduled_transfer_list: List[MonthlyFinanceTransfer]
    savings: MonthlyFinanceTransfer

    @staticmethod
    def get_from_monthly_finances(monthly_finances: monthly_financial_organisation.MonthlyFinances) -> "MonthlyFinances":
        return MonthlyFinances(
            salary=monthly_finances.salary,
            needs=monthly_finances.needs,
            wants=monthly_finances.wants,
            needs_transfer_list=[MonthlyFinanceTransfer.get_from_transfer(transfer) for transfer in monthly_finances.needs_transfer_list],
            wants_transfer_list=[MonthlyFinanceTransfer.get_from_transfer(transfer) for transfer in monthly_finances.wants_transfer_list],
            scheduled_transfer_list=[MonthlyFinanceTransfer.get_from_transfer(transfer) for transfer in monthly_finances.scheduled_transfer_list],
            savings=MonthlyFinanceTransfer.get_from_transfer(monthly_finances.savings)
        )
