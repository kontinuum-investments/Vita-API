import datetime
from enum import Enum

from _decimal import Decimal
from sirius.common import DataClass


class DailyFinances(DataClass):
    monthly_budget: Decimal
    daily_budget: Decimal
    is_over_budget: bool
    amount_under_budget: Decimal | None = None
    amount_over_budget: Decimal | None = None
    date_budget_reached: datetime.date | None = None


class BalanceUpdateType(Enum):
    CREDIT: str = "credit"
    DEBIT: str = "debit"


class Resource(DataClass):
    id: int
    profile_id: int
    type: str


class Data(DataClass):
    resource: Resource
    amount: float
    currency: str
    post_transaction_balance_amount: float
    occurred_at: str
    transaction_type: BalanceUpdateType


class WiseBalanceUpdate(DataClass):
    data: Data
    subscription_id: str
    event_type: str
    schema_version: str
    sent_at: str
