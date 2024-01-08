import asyncio
import json
from decimal import Decimal
from typing import Optional, List, Dict, Any, cast

from sirius import excel, common
from sirius.common import DataClass, Currency
from sirius.communication.logger import Logger
from sirius.wise import AccountCredit, AccountDebit, WiseAccount, WiseAccountType, ReserveAccount, WiseWebhook, Transaction, CashAccount
from starlette.requests import Request

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.common import FinancesSettings, PlannedExpense
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


class SharedExpense(DataClass):
    recipient_name: str | None
    name_in_statement: str | None
    reserve_account: ReserveAccount
    notification_phone_number: str | None
    is_unknown_recipient: bool = False
    merchant_list: List[str] = []

    async def do_planned_shared_expense(self, transaction: Transaction, planned_expense: PlannedExpense | None = None) -> None:
        nzd_account: CashAccount = cast(CashAccount, transaction.account)
        each_share: Decimal = transaction.amount / Decimal("-2")
        remitter_reserve_account: ReserveAccount = self.reserve_account
        remitter_reserve_account_amount_to_transfer: Decimal = min(remitter_reserve_account.balance, each_share)

        if planned_expense is None:
            await FinancesSettings.top_up_cash_reserve_from_daily_expense_reserve_account(nzd_account.profile.wise_account, each_share)
        else:
            await planned_expense.do_planned_expense(each_share)

        await remitter_reserve_account.transfer(nzd_account, remitter_reserve_account_amount_to_transfer)

        if each_share > remitter_reserve_account_amount_to_transfer:
            amount_short_of = each_share - remitter_reserve_account_amount_to_transfer
            await FinancesSettings.top_up_cash_reserve_from_daily_expense_reserve_account(nzd_account.profile.wise_account, amount_short_of)
            asyncio.ensure_future(Discord.send_message(DiscordTextChannel.HOUSEHOLD_FINANCES,
                                                       f"**Insufficient funds for Shared Expense**\n"
                                                       f"*Shared Amount*: {transaction.account.currency.value} {common.get_decimal_str(transaction.amount * Decimal("-1"))}\n"
                                                       f"*{self.recipient_name}'s Share*: {transaction.account.currency.value} {common.get_decimal_str(each_share)}\n"
                                                       f"*Short of*: {transaction.account.currency.value} {common.get_decimal_str(amount_short_of)}\n"
                                                       ))
        else:
            asyncio.ensure_future(Discord.send_message(DiscordTextChannel.HOUSEHOLD_FINANCES,
                                                       f"**Shared Expense**\n"
                                                       f"*Shared Expense Amount*: {transaction.account.currency.value} {common.get_decimal_str(transaction.amount)}\n"
                                                       f"*Each Share*: {transaction.account.currency.value} {common.get_decimal_str(each_share)}\n"
                                                       f"*Balance in {self.recipient_name}'s Account*: {remitter_reserve_account.currency.value} {common.get_decimal_str(remitter_reserve_account.balance)}\n"
                                                       ))

    @staticmethod
    def get(transaction: Transaction) -> Optional["SharedExpense"]:
        shared_expense: SharedExpense | None = None
        if isinstance(transaction.third_party, str):
            name_in_statement: str = transaction.third_party.split(" |")[0]
            shared_expense = SharedExpense.get_by_name_in_statement(name_in_statement, transaction.account.profile.wise_account)

        if shared_expense is None:
            reserve_account: ReserveAccount = transaction.account.profile.wise_account.personal_profile.get_reserve_account(
                f"Unknown [Reserve]", transaction.account.currency, True)
            shared_expense = SharedExpense(
                recipient_name=None,
                name_in_statement=None,
                reserve_account=reserve_account,
                is_unknown_recipient=True,
                notification_phone_number=None
            )

        return shared_expense

    @staticmethod
    def get_all(wise_account: WiseAccount | None = None, excel_file_path: str | None = None) -> List["SharedExpense"]:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path
        raw_remitter_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Shared Expenses")
        shared_expense_list: List[SharedExpense] = []

        for raw_remitter in raw_remitter_list:
            recipient_name: str = raw_remitter["Remitter's Name"]
            currency: Currency = Currency(raw_remitter["Currency"])
            reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(f"{recipient_name} [Reserve]", currency, True)

            shared_expense_list.append(SharedExpense(
                recipient_name=recipient_name,
                name_in_statement=raw_remitter["Name in Statement"],
                reserve_account=reserve_account,
                notification_phone_number=raw_remitter["Notification Phone Number"],
                merchant_list=raw_remitter["Shared Expense Merchants"].split("\n") if raw_remitter["Shared Expense Merchants"] is not None else []
            ))

        return shared_expense_list

    @staticmethod
    def get_by_name_in_statement(name_in_statement: str, wise_account: WiseAccount | None = None, excel_file_path: str | None = None) -> Optional["SharedExpense"]:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path

        try:
            return next(filter(lambda e: e.name_in_statement.lower() == name_in_statement.lower().split(" | ")[0], SharedExpense.get_all(wise_account, excel_file_path)))
        except StopIteration:
            return None

    @staticmethod
    def get_by_merchant_name(merchant_name: str, wise_account: WiseAccount | None = None, excel_file_path: str | None = None) -> Optional["SharedExpense"]:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path

        try:
            return next(filter(lambda e: any(merchant_name.lower() == m.lower() for m in e.merchant_list), SharedExpense.get_all(wise_account, excel_file_path)))
        except StopIteration:
            return None
