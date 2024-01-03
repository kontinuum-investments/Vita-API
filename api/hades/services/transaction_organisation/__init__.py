import asyncio
import json
from typing import Optional, List, Dict, Any

from sirius import excel, common
from sirius.common import DataClass, Currency
from sirius.communication import sms
from sirius.communication.logger import Logger
from sirius.wise import AccountCredit, AccountDebit, WiseAccount, WiseAccountType, ReserveAccount, WiseWebhook
from starlette.requests import Request

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.common import FinancesSettings
from api.hades.models.database import WiseAccountUpdate


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
            account_update: AccountDebit | AccountCredit | None = await WiseWebhook.get_balance_update_object(request_data, wise_account)
        except Exception:
            await Logger.debug(f"Un-parsable Wise account update received:\n{json.dumps(request_data)}")
            return

        if isinstance(account_update, AccountCredit):
            asyncio.ensure_future(WiseCreditEvent.do(account_update))
        elif isinstance(account_update, AccountDebit):
            asyncio.ensure_future(WiseDebitEvent.do(account_update))

        asyncio.ensure_future(WiseAccountUpdate(wise_delivery_id=wise_delivery_id).save())


class WiseCreditEvent:
    @staticmethod
    async def do(account_credit: AccountCredit) -> None:
        expected_remitter: ExpectedRemitter | None = ExpectedRemitter.get(account_credit)
        await account_credit.account.transfer(expected_remitter.reserve_account, account_credit.transaction.amount)
        if expected_remitter.notification_phone_number is not None:
            asyncio.ensure_future(sms.send_message(expected_remitter.notification_phone_number, f"A fund transfer of {account_credit.account.currency.value} {common.get_decimal_str(account_credit.transaction.amount)} has been "
                                                                                                 f"received.\nThis is an automated message from Athena."))

        asyncio.ensure_future(Discord.send_message(DiscordTextChannel.WISE, f"**Account Credited**\n"
                                                                            f"*From*: {account_credit.transaction.third_party if expected_remitter.is_unknown_recipient else expected_remitter.recipient_name}\n"
                                                                            f"*Amount*: {account_credit.account.currency.value} {common.get_decimal_str(account_credit.transaction.amount)}\n"
                                                                            f"*Reserve Account Balance*: {account_credit.account.currency.value} {common.get_decimal_str(expected_remitter.reserve_account.balance)}"))

        FinancesSettings.notify_if_only_cash_reserve_amount_present(account_credit.account.profile.wise_account)


class WiseDebitEvent:
    @staticmethod
    async def do(account_debit: AccountDebit) -> None:
        FinancesSettings.notify_if_only_cash_reserve_amount_present(account_debit.account.profile.wise_account)


class ExpectedRemitter(DataClass):
    recipient_name: str | None
    name_in_statement: str | None
    reserve_account: ReserveAccount
    notification_phone_number: str | None
    is_unknown_recipient: bool = False

    @staticmethod
    def get(account_credit: AccountCredit) -> Optional["ExpectedRemitter"]:
        expected_remitter: ExpectedRemitter | None = None
        if isinstance(account_credit.transaction.third_party, str):
            name_in_statement: str = account_credit.transaction.third_party.split(" |")[0]
            expected_remitter = ExpectedRemitter._get_by_name_in_statement(name_in_statement, account_credit.account.profile.wise_account)

        if expected_remitter is None:
            reserve_account: ReserveAccount = account_credit.account.profile.wise_account.personal_profile.get_reserve_account(f"Unknown [Reserve]", account_credit.account.currency, True)
            expected_remitter = ExpectedRemitter(
                recipient_name=None,
                name_in_statement=None,
                reserve_account=reserve_account,
                is_unknown_recipient=True,
                notification_phone_number=None
            )

        return expected_remitter

    @staticmethod
    def get_all(wise_account: WiseAccount | None = None) -> List["ExpectedRemitter"]:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        excel_file_path: str = FinancesSettings.get_monthly_finances_excel_file_path()
        raw_remitter_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Expected Remitters")
        expected_remitter_list: List[ExpectedRemitter] = []

        for raw_remitter in raw_remitter_list:
            recipient_name: str = raw_remitter["Remitter's Name"]
            currency: Currency = Currency(raw_remitter["Currency"])
            reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(f"{recipient_name} [Reserve]", currency, True)

            expected_remitter_list.append(ExpectedRemitter(
                recipient_name=recipient_name,
                name_in_statement=raw_remitter["Name in Statement"],
                reserve_account=reserve_account,
                notification_phone_number=raw_remitter["Notification Phone Number"]
            ))

        return expected_remitter_list

    @staticmethod
    def _get_by_name_in_statement(name_in_statement: str, wise_account: WiseAccount) -> Optional["ExpectedRemitter"]:
        try:
            return next(filter(lambda e: e.name_in_statement.lower() == name_in_statement.lower(), ExpectedRemitter.get_all(wise_account)))
        except StopIteration:
            return None
