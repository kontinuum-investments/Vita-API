import datetime

from _decimal import Decimal
from sirius import wise
from sirius.common import DataClass


class DailyFinances(DataClass):
    monthly_budget: Decimal
    daily_budget: Decimal
    is_over_budget: bool
    amount_under_budget: Decimal | None = None
    amount_over_budget: Decimal | None = None
    date_budget_reached: datetime.date | None = None


class WiseWebHook(DataClass):
    data: wise.Account
    subscription_id: str
    event_type: str
    schema_version: str
    sent_at: str
