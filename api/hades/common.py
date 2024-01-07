import asyncio
import calendar
import datetime
import os
from abc import ABC
from decimal import Decimal, ROUND_UP, ROUND_DOWN
from enum import Enum
from typing import Dict, Any, Tuple, List, Optional, cast, TYPE_CHECKING

from sirius import common, excel
from sirius.common import Currency, DataClass
from sirius.communication import sms
from sirius.exceptions import SDKClientException
from sirius.wise import WiseAccount, WiseAccountType, CashAccount, ReserveAccount, Recipient, Account, Quote, \
    Transaction

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.common import EnvironmentalSecret
from api.exceptions import ClientException

if TYPE_CHECKING:
    from api.hades.services.transaction_organisation import SharedExpense


class FinancesSettings:

    @staticmethod
    def get_monthly_finances_excel_file_path() -> str:
        #   TODO: Integrate OneDrive API
        download_file_line: str = common.get_environmental_secret(
            EnvironmentalSecret.MONTHLY_FINANCES_EXCEL_FILE_LINK.value) + "&download=1"
        excel_file_path: str = common.download_file_from_url(download_file_line)
        new_excel_file_path: str = f"{excel_file_path}.xlsx"
        os.rename(excel_file_path, new_excel_file_path)
        return new_excel_file_path

    @staticmethod
    def get_settings() -> Dict[str, Any]:
        settings: Dict[str, Any] = {}
        for raw_setting in excel.get_excel_data(FinancesSettings.get_monthly_finances_excel_file_path(), "Settings"):
            key: str | None = raw_setting.get("Key")
            value: Any | None = raw_setting.get("Value")
            if key is not None and value is not None:
                settings[key] = value

        return settings

    @staticmethod
    def get_cash_reserve_amount() -> Decimal:
        cash_reserve_amount: Any = FinancesSettings.get_settings()["Cash Reserve"]
        if cash_reserve_amount is None or not isinstance(cash_reserve_amount, Decimal):
            raise ClientException("Could not find a valid cash reserve amount in Finance Settings")

        return cash_reserve_amount

    @staticmethod
    def notify_if_only_cash_reserve_amount_present(wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        cash_reserve_amount: Decimal = FinancesSettings.get_cash_reserve_amount()
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)

        if nzd_account.balance != cash_reserve_amount:
            asyncio.ensure_future(Discord.notify_error("Validating Cash Reserve",
                                                       f"*Expected Amount*: {nzd_account.currency.value} {common.get_decimal_str(cash_reserve_amount)}\n"
                                                       f"*Actual Amount*: {nzd_account.currency.value} {common.get_decimal_str(nzd_account.balance)}"))

    @staticmethod
    async def top_up_cash_reserve_from_daily_expense_reserve_account(wise_account: WiseAccount | None = None, amount: Decimal | None = None) -> None:
        cash_reserve_amount: Decimal = FinancesSettings.get_cash_reserve_amount()
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        daily_expense: PlannedExpense = PlannedExpense.get(PlannedExpenseNeed.DAILY_EXPENSES, wise_account)
        reserve_account: ReserveAccount = daily_expense.reserve_account

        if nzd_account.balance < cash_reserve_amount or amount is not None:
            await reserve_account.transfer(nzd_account, cash_reserve_amount - nzd_account.balance if amount is None else amount)

        amount_within_budget: Decimal = reserve_account.balance - FinancesSettings._expected_amount_in_daily_expense_reserve_account(wise_account, daily_expense)
        message_title: str = "**Daily Budget Notification**\n"
        if amount_within_budget < Decimal("0"):
            amount_out_of_budget: Decimal = amount_within_budget * Decimal("-1")
            number_of_days_to_catch_up: Decimal = (amount_out_of_budget / FinancesSettings._get_daily_budget(wise_account, daily_expense)).quantize(Decimal("0"), rounding=ROUND_UP)
            catch_up_date: datetime.date = datetime.date.today() + datetime.timedelta(days=int(number_of_days_to_catch_up))

            asyncio.ensure_future(Discord.notify(f"{message_title}*Amount over budget*: {reserve_account.currency.value}{common.get_decimal_str(amount_out_of_budget)}\n"
                                                 f"*Date when under budget*: {common.get_date_string(catch_up_date)} ({number_of_days_to_catch_up} days)"))
        else:
            asyncio.ensure_future(Discord.notify(f"{message_title}*Amount within budget*: {reserve_account.currency.value}{common.get_decimal_str(amount_within_budget)}"))

    @staticmethod
    def _get_daily_budget(wise_account: WiseAccount, daily_expense: Optional["PlannedExpense"] = None,
                          date: datetime.date | None = None) -> Decimal:
        daily_expense = PlannedExpense.get(PlannedExpenseNeed.DAILY_EXPENSES,
                                           wise_account) if daily_expense is None else daily_expense
        date = datetime.date.today() if date is None else date
        number_of_days_in_month: Decimal = Decimal(calendar.monthrange(date.year, date.month)[1])
        return (daily_expense.amount / number_of_days_in_month).quantize(Decimal("0.00"), rounding=ROUND_DOWN)

    @staticmethod
    def _expected_amount_in_daily_expense_reserve_account(wise_account: WiseAccount,
                                                          daily_expense: Optional["PlannedExpense"] = None,
                                                          date: datetime.date | None = None) -> Decimal:
        date = datetime.date.today() if date is None else date
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        monthly_budget = PlannedExpense.get(PlannedExpenseNeed.DAILY_EXPENSES, wise_account).amount

        daily_budget: Decimal = FinancesSettings._get_daily_budget(wise_account, daily_expense, date)
        amount_to_spend: Decimal = Decimal(date.day) * daily_budget.quantize(Decimal("0.00"), rounding=ROUND_UP)
        return (monthly_budget - amount_to_spend).quantize(Decimal("0.00"), rounding=ROUND_UP)


class PlannedExpenseType(Enum):
    NEEDS: str = "Needs"
    WANTS: str = "Wants"
    SCHEDULED: str = "Scheduled"


class PlannedExpenseTitle(Enum):
    pass


class PlannedExpenseNeed(PlannedExpenseTitle):
    DAILY_EXPENSES: str = "Daily Expenses"
    RENT: str = "Rent"
    MOBILE_BILL: str = "Mobile Bill"
    CAR_INSURANCE: str = "Car Insurance"
    VEHICLE_MAINTENANCE: str = "Vehicle Maintenance"
    UTILITIES: str = "Utilities"


class PlannedExpenseWant(PlannedExpenseTitle):
    pass


class PlannedExpenseScheduled(PlannedExpenseTitle):
    pass


class PlannedExpense(DataClass):
    description: str
    amount: Decimal
    reserve_account: ReserveAccount | None = None
    recipient: Recipient | None = None
    notification_phone_number: str | None = None
    merchant: str | None = None

    def do_scheduled_planned_expense(self) -> None:
        nzd_account: CashAccount = self.reserve_account.profile.get_cash_account(Currency.NZD)
        self.reserve_account.transfer(nzd_account, self.amount)
        asyncio.ensure_future(sms.send_message(self.notification_phone_number,
                                               f"{self.reserve_account.currency.value}{common.get_decimal_str(self.amount)} has been transferred to your account.\n"
                                               f"This is an automated message from Athena."))

    async def do_planned_expense(self, amount_to_transfer: Decimal | None = None) -> None:
        amount_to_transfer = self.amount if amount_to_transfer is None else amount_to_transfer
        wise_account: WiseAccount = self.reserve_account.profile.wise_account
        nzd_account: CashAccount = cast(CashAccount, wise_account.personal_profile.get_cash_account(Currency.NZD))
        reserve_account: ReserveAccount = self.reserve_account
        reserve_account_amount_to_transfer: Decimal = min(reserve_account.balance, amount_to_transfer)

        if amount_to_transfer > reserve_account_amount_to_transfer:
            amount_short_of: Decimal = amount_to_transfer - reserve_account.balance
            await FinancesSettings.top_up_cash_reserve_from_daily_expense_reserve_account(nzd_account.profile.wise_account, amount_short_of)

            asyncio.ensure_future(Discord.notify(f"**Insufficient funds for Shared Planned Expense**\n"
                                                 f"*Total Planned Expense Amount*: {reserve_account.currency.value} {common.get_decimal_str(amount_to_transfer)}\n"
                                                 f"*Balance in Reserve Account*: {reserve_account.currency.value} {common.get_decimal_str(reserve_account.balance)}\n"
                                                 f"*Short of*: {reserve_account.currency.value} {common.get_decimal_str(amount_short_of)}\n"
                                                 ))

        if reserve_account_amount_to_transfer > Decimal("0"):
            await reserve_account.transfer(nzd_account, reserve_account_amount_to_transfer)

    @staticmethod
    def get_all(wise_account: WiseAccount | None = None, excel_file_path: str | None = None) -> Tuple[List["PlannedExpense"], List["PlannedExpense"], List["PlannedExpense"], "PlannedExpense"]:
        from api.hades.services.monthly_financial_organisation import MonthlyFinances

        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path
        salary: Decimal = MonthlyFinances.get_salary(excel_file_path)
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        needs_planned_expense_list, wants_planned_expense_list = PlannedExpense._get_needs_and_wants_list(wise_account,
                                                                                                          excel_file_path)
        scheduled_planned_expense_list: List[PlannedExpense] = PlannedExpense._get_scheduled_list(wise_account,
                                                                                                  excel_file_path)
        savings_amount: Decimal = PlannedExpense._get_savings_amount(needs_planned_expense_list + wants_planned_expense_list + scheduled_planned_expense_list, salary, wise_account)
        savings: PlannedExpense = PlannedExpense(
            description="Savings",
            amount=savings_amount,
            recipient=PlannedExpense._get_savings_recipient(wise_account)
        )

        return needs_planned_expense_list, wants_planned_expense_list, scheduled_planned_expense_list, savings

    @staticmethod
    def get(planned_expense_title: PlannedExpenseTitle, wise_account: WiseAccount | None = None) -> "PlannedExpense":
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        planned_expense_type: PlannedExpenseType = PlannedExpense._get_planned_expense_type_from_planned_expense_title(planned_expense_title)
        reserve_account_name: str = f"{planned_expense_title.value}{PlannedExpense._get_reserve_account_suffix(planned_expense_type)}"
        needs_planned_expense_list, wants_planned_expense_list, scheduled_planned_expense_list, savings = PlannedExpense.get_all(wise_account)

        if planned_expense_type == planned_expense_type.NEEDS:
            return next(filter(lambda e: e.reserve_account.name == reserve_account_name, needs_planned_expense_list))
        elif planned_expense_type == planned_expense_type.WANTS:
            return next(filter(lambda e: e.reserve_account.name == reserve_account_name, wants_planned_expense_list))
        elif planned_expense_type == planned_expense_type.SCHEDULED:
            return next(
                filter(lambda e: e.reserve_account.name == reserve_account_name, scheduled_planned_expense_list))

        raise SDKClientException(f"Unknown planned expense: {planned_expense_title.value}")

    @staticmethod
    def get_by_merchant_name(merchant_name: str, wise_account: WiseAccount | None = None,
                             excel_file_path: str | None = None) -> Optional["PlannedExpense"]:
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path
        needs_planned_expense_list, wants_planned_expense_list = PlannedExpense.get_all(wise_account,
                                                                                        excel_file_path=excel_file_path)[
                                                                 :2]

        try:
            return next(filter(lambda e: e.merchant is not None and merchant_name.lower() == e.merchant.lower(),
                               needs_planned_expense_list + wants_planned_expense_list))
        except StopIteration:
            return None

    @staticmethod
    def _get_planned_expense_type_from_planned_expense_title(
            planned_expense_title: PlannedExpenseTitle) -> PlannedExpenseType:
        if isinstance(planned_expense_title, PlannedExpenseNeed):
            return PlannedExpenseType.NEEDS
        elif isinstance(planned_expense_title, PlannedExpenseWant):
            return PlannedExpenseType.WANTS
        elif isinstance(planned_expense_title, PlannedExpenseScheduled):
            return PlannedExpenseType.SCHEDULED

        raise SDKClientException(f"Unknown planned expense: {planned_expense_title.value}")

    @staticmethod
    def _get_needs_and_wants_list(wise_account: WiseAccount, excel_file_path: str | None = None) -> Tuple[
        List["PlannedExpense"], List["PlannedExpense"]]:
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path
        planned_expense_list: List[PlannedExpense] = []
        wants_planned_expense_list: List[PlannedExpense] = []

        for planned_expense_type in [PlannedExpenseType.NEEDS, PlannedExpenseType.WANTS]:
            raw_planned_expense_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path,
                                                                                  planned_expense_type.value)
            for raw_planned_expense in raw_planned_expense_list:
                description: str = raw_planned_expense["Description"]
                currency: Currency = Currency(raw_planned_expense["Currency"])
                planned_expense: PlannedExpense = PlannedExpense(
                    description=raw_planned_expense["Description"],
                    amount=raw_planned_expense["Amount"],
                    reserve_account=wise_account.personal_profile.get_reserve_account(
                        f"{description}{PlannedExpense._get_reserve_account_suffix(planned_expense_type)}", currency,
                        True),
                    merchant=raw_planned_expense["Merchant"]
                )

                if planned_expense_type == PlannedExpenseType.NEEDS:
                    planned_expense_list.append(planned_expense)
                elif planned_expense_type == PlannedExpenseType.WANTS:
                    wants_planned_expense_list.append(planned_expense)

        return planned_expense_list, wants_planned_expense_list

    @staticmethod
    def _get_scheduled_list(wise_account: WiseAccount, excel_file_path: str | None = None) -> List["PlannedExpense"]:
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path
        raw_scheduled_planned_expense_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path,
                                                                                        "Scheduled Transfers")
        planned_expense_list: List[PlannedExpense] = []

        for raw_scheduled_planned_expense in raw_scheduled_planned_expense_list:
            description: str = raw_scheduled_planned_expense["Description"]
            amount: Decimal = raw_scheduled_planned_expense["Amount"]
            recipient: Recipient = wise_account.personal_profile.get_recipient(
                raw_scheduled_planned_expense["Account Number"].replace("~", ""))
            assert recipient.currency == Currency(raw_scheduled_planned_expense["Currency"])

            planned_expense_list.append(PlannedExpense(
                description=description,
                amount=amount,
                recipient=recipient,
                notification_phone_number=raw_scheduled_planned_expense["Notification Phone Number"]
            ))

        return planned_expense_list

    @staticmethod
    def _get_savings_amount(planned_expense_list: List["PlannedExpense"], salary: Decimal,
                            wise_account: WiseAccount) -> Decimal:
        nzd_balance: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        savings_amount: Decimal = salary

        for planned_expense in planned_expense_list:
            to_account: Account | Recipient = planned_expense.reserve_account if planned_expense.reserve_account is not None else planned_expense.recipient
            if to_account.currency == nzd_balance.currency:
                savings_amount = savings_amount - planned_expense.amount
            else:
                quote: Quote = Quote.get_quote(wise_account.personal_profile, nzd_balance, to_account,
                                               planned_expense.amount)
                savings_amount = savings_amount - quote.from_amount

        return savings_amount

    @staticmethod
    def _get_savings_recipient(wise_account: WiseAccount) -> Recipient:
        account_number: str = FinancesSettings.get_settings()["Savings Account Number"]
        return wise_account.personal_profile.get_recipient(account_number)

    @staticmethod
    def _get_reserve_account_suffix(planned_expense_type: PlannedExpenseType) -> str:
        return f" ({planned_expense_type.value})"
