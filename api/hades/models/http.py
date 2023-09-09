import datetime
from enum import Enum

from _decimal import Decimal
from sirius import wise
from sirius.common import DataClass, Currency


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


class BalanceUpdateResource(DataClass):
    type: str
    id: int
    profile_id: int


class BalanceUpdateData(DataClass):
    resource: BalanceUpdateResource
    amount: Decimal
    currency: Currency
    transaction_type: BalanceUpdateType
    occurred_at: datetime.datetime
    transfer_reference: str | None = None
    channel_name: str | None = None


class WiseWebHook(DataClass):
    data: BalanceUpdateData
    subscription_id: str
    event_type: wise.WebhookAccountUpdateType
    schema_version: str
    sent_at: datetime.datetime
