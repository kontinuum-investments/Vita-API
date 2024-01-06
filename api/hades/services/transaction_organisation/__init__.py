import asyncio
import json
from typing import Optional, List, Dict, Any

from sirius import excel, common
from sirius.common import DataClass, Currency
from sirius.communication.logger import Logger
from sirius.wise import AccountCredit, AccountDebit, WiseAccount, WiseAccountType, ReserveAccount, WiseWebhook, Transaction
from starlette.requests import Request

from api.hades.common import FinancesSettings
from api.hades.models.database import WiseAccountUpdate
from api.hades.services.transaction_organisation.credit import WiseCreditEvent
from api.hades.services.transaction_organisation.debit import WiseDebitEvent


class AccountUpdate:

    @classmethod
    async def handle_account_update(cls, request: Request) -> None:
        request_data: Dict[str, Any] = await request.json()
        asyncio.ensure_future(Logger.debug(f"Wise account update received:\n{json.dumps(request_data)}"))
        asyncio.ensure_future(AccountUpdate.do(request_data, request.headers["X-Delivery-Id"]))

    @staticmethod
    async def do(request_data: Dict[str, Any], wise_delivery_id: str) -> None:
        if not common.is_development_environment() and await WiseAccountUpdate.is_duplicate(wise_delivery_id):
            await Logger.debug(f"Duplicate Wise account update received:\n{json.dumps(request_data)}")
            return

        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        try:
            account_update: AccountDebit | AccountCredit | None = WiseWebhook.get_balance_update_object(request_data, wise_account)
        except Exception:
            await Logger.debug(f"Un-parsable Wise account update received:\n{json.dumps(request_data)}")
            return

        if isinstance(account_update, AccountCredit):
            asyncio.ensure_future(WiseCreditEvent.do(account_update.transaction))
        elif isinstance(account_update, AccountDebit) and account_update.is_successful:
            asyncio.ensure_future(WiseDebitEvent.do(account_update.transaction))

        asyncio.ensure_future(WiseAccountUpdate(wise_delivery_id=wise_delivery_id).save())


class ExpectedRemitter(DataClass):
    recipient_name: str | None
    name_in_statement: str | None
    reserve_account: ReserveAccount
    notification_phone_number: str | None
    is_unknown_recipient: bool = False

    @staticmethod
    def get(transaction: Transaction) -> Optional["ExpectedRemitter"]:
        expected_remitter: ExpectedRemitter | None = None
        if isinstance(transaction.third_party, str):
            name_in_statement: str = transaction.third_party.split(" |")[0]
            expected_remitter = ExpectedRemitter.get_by_name_in_statement(name_in_statement, transaction.account.profile.wise_account)

        if expected_remitter is None:
            reserve_account: ReserveAccount = transaction.account.profile.wise_account.personal_profile.get_reserve_account(
                f"Unknown [Reserve]", transaction.account.currency, True)
            expected_remitter = ExpectedRemitter(
                recipient_name=None,
                name_in_statement=None,
                reserve_account=reserve_account,
                is_unknown_recipient=True,
                notification_phone_number=None
            )

        return expected_remitter

    @staticmethod
    def get_all(wise_account: WiseAccount | None = None, excel_file_path: str | None = None) -> List["ExpectedRemitter"]:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path
        raw_remitter_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Expected Remitters")
        expected_remitter_list: List[ExpectedRemitter] = []

        for raw_remitter in raw_remitter_list:
            recipient_name: str = raw_remitter["Remitter's Name"]
            currency: Currency = Currency(raw_remitter["Currency"])
            reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(
                f"{recipient_name} [Reserve]", currency, True)

            expected_remitter_list.append(ExpectedRemitter(
                recipient_name=recipient_name,
                name_in_statement=raw_remitter["Name in Statement"],
                reserve_account=reserve_account,
                notification_phone_number=raw_remitter["Notification Phone Number"]
            ))

        return expected_remitter_list

    @staticmethod
    def get_by_name_in_statement(name_in_statement: str, wise_account: WiseAccount) -> Optional["ExpectedRemitter"]:
        try:
            return next(filter(lambda e: e.name_in_statement.lower() == name_in_statement.lower().split(" | ")[0],
                               ExpectedRemitter.get_all(wise_account)))
        except StopIteration:
            return None
