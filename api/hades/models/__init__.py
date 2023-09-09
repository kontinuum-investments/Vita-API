import datetime
from typing import Dict, Any

from sirius import wise
from sirius.common import DataClass, Currency
from sirius.wise import WiseAccount, WiseAccountType, PersonalProfile, CashAccount


class AccountCredit(DataClass):
    account: wise.CashAccount
    is_attempted: bool
    is_successful: bool
    timestamp: datetime.datetime

    @staticmethod
    def get_from_request_data(request_data: Dict[str, Any]) -> "AccountCredit":
        personal_profile: PersonalProfile = WiseAccount.get(WiseAccountType.PRIMARY).personal_profile
        cash_account: CashAccount = next(filter(lambda c: c.id == request_data["data"]["resource"]["account_id"], personal_profile.cash_account_list))

        return AccountCredit(account=cash_account,
                             is_attempted=request_data["data"]["current_state"] == "incoming_payment_waiting",
                             is_successful=request_data["data"]["current_state"] == "outgoing_payment_sent",
                             timestamp=request_data["data"]["occurred_at"])


class AccountDebit(DataClass):
    id: int
    account: wise.CashAccount
    timestamp: datetime.datetime

    @staticmethod
    def get_from_request_data(request_data: Dict[str, Any]) -> "AccountDebit":
        personal_profile: PersonalProfile = WiseAccount.get(WiseAccountType.PRIMARY).personal_profile
        cash_account: wise.CashAccount = personal_profile.get_cash_account(Currency(request_data["data"]["currency"]))
        return AccountDebit(id=request_data["data"]["resource"]["id"], account=cash_account, timestamp=request_data["data"]["occurred_at"])
