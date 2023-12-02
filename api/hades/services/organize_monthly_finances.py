import datetime
import os
from typing import List, Any, Dict, Tuple, cast

import sirius
from _decimal import Decimal
from sirius import excel
from sirius.common import DataClass, Currency
from sirius.wise import ReserveAccount, Recipient, WiseAccount, WiseAccountType, CashAccount

from api import common
from api.athena.services.discord import Discord
from api.common import EnvironmentalSecret
from api.exceptions import ClientException
from api.hades.constants import WiseReserveAccount


class Summary(DataClass):
    salary: Decimal
    total_needs_expenses: Decimal
    total_wants_expenses: Decimal
    total_expenses: Decimal
    savings: Decimal

    @staticmethod
    def get(excel_file_path: str) -> "Summary":
        excel_data: Dict[Any, Any] = excel.get_key_value_pair(excel_file_path, "Summary")
        return Summary(salary=excel_data["Salary"],
                       total_needs_expenses=excel_data["Needs Expenses"],
                       total_wants_expenses=excel_data["Wants Expenses"],
                       total_expenses=excel_data["Total Expenses"],
                       savings=excel_data["Total Savings"])


class Settings(DataClass):
    salary: Decimal
    maximum_expenditure: Decimal
    monthly_needs_budget: Decimal
    monthly_wants_budget: Decimal
    fixed_expenses_account: Recipient
    month: datetime.date

    @staticmethod
    def get(excel_file_path: str, wise_account: WiseAccount) -> "Settings":
        excel_data: Dict[Any, Any] = excel.get_key_value_pair(excel_file_path, "Settings")
        return Settings(salary=cast(Decimal, excel_data["Salary"]),
                        maximum_expenditure=excel_data["Maximum Expenditure"],
                        monthly_needs_budget=excel_data["Monthly Needs Budget"],
                        monthly_wants_budget=excel_data["Monthly Wants Budget"],
                        fixed_expenses_account=wise_account.personal_profile.get_recipient(excel_data["Fixed Expenses Account Number"]),
                        savings_account=wise_account.personal_profile.get_recipient(excel_data["Savings Account Number"]),
                        month=excel_data["Month"])

    savings_account: Recipient


class FixedExpense(DataClass):
    description: str
    amount: Decimal
    currency: Currency


class Reserve(DataClass):
    reserve_account: ReserveAccount
    amount: Decimal


class ScheduledTransfer(DataClass):
    recipient: Recipient
    amount: Decimal


class MonthlyFinances(DataClass):
    excel_file_path: str
    fixed_expenses_need_list: List[FixedExpense]
    fixed_expenses_want_list: List[FixedExpense]
    reserve_need_list: List[Reserve]
    reserve_want_list: List[Reserve]
    scheduled_transfer_list: List[ScheduledTransfer]
    settings: Settings
    summary: Summary

    @staticmethod
    def _get_fixed_expenses(excel_file_path: str) -> Tuple[List[FixedExpense], List[FixedExpense]]:
        fixed_expenses_need_list: List[FixedExpense] = []
        fixed_expenses_want_list: List[FixedExpense] = []

        for sheet_name in ["Fixed Expenses (Needs)", "Fixed Expenses (Wants)"]:
            excel_data: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, sheet_name)
            fixed_expense_list: List[FixedExpense] = [FixedExpense(description=data["Description"], amount=data["Amount"], currency=Currency(data["Currency"])) for data in excel_data]
            fixed_expenses_need_list = fixed_expense_list if "need" in sheet_name.lower() else fixed_expenses_need_list
            fixed_expenses_want_list = fixed_expense_list if "want" in sheet_name.lower() else fixed_expenses_want_list

        return fixed_expenses_need_list, fixed_expenses_want_list

    @staticmethod
    def _get_reserve(excel_file_path: str, wise_account: WiseAccount) -> Tuple[List[Reserve], List[Reserve]]:
        reserve_need_list: List[Reserve] = []
        reserve_want_list: List[Reserve] = []

        for sheet_name in ["Reserve (Needs)", "Reserve (Wants)"]:
            excel_data: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, sheet_name)
            reserve_list: List[Reserve] = []

            for data in excel_data:
                reserve_account_name: str = data["Description"] + (" (Needs)" if "need" in sheet_name.lower() else " (Wants)")
                reserve_list.append(Reserve(
                    reserve_account=wise_account.personal_profile.get_reserve_account(reserve_account_name, Currency(data["Currency"]), True),
                    amount=data["Amount"]
                ))

            reserve_need_list = reserve_list if "need" in sheet_name.lower() else reserve_need_list
            reserve_want_list = reserve_list if "want" in sheet_name.lower() else reserve_want_list

        return reserve_need_list, reserve_want_list

    @staticmethod
    def _get_scheduled_transfer_list(excel_file_path: str, wise_account: WiseAccount) -> List[ScheduledTransfer]:
        excel_data: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Scheduled Transfers")
        return [ScheduledTransfer(recipient=wise_account.personal_profile.get_recipient(data["Account Number"]),
                                  amount=data["Amount"]) for data in excel_data]

    @staticmethod
    async def _transfer_scheduled_transfers(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        [await nzd_account.transfer(scheduled_transfer.recipient, scheduled_transfer.amount) for scheduled_transfer in monthly_finances.scheduled_transfer_list]

    @staticmethod
    async def _transfer_reserves(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        [await nzd_account.transfer(reserve.reserve_account, reserve.amount) for reserve in monthly_finances.reserve_need_list + monthly_finances.reserve_want_list]

    @staticmethod
    async def _transfer_fixed_expenses(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        total_fixed_expenses: Decimal = Decimal("0")

        for fixed_expense in monthly_finances.fixed_expenses_need_list + monthly_finances.fixed_expenses_want_list:
            total_fixed_expenses = total_fixed_expenses + fixed_expense.amount

        await nzd_account.transfer(monthly_finances.settings.fixed_expenses_account, total_fixed_expenses)

    @staticmethod
    async def _reserve_next_months_expenses(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(WiseReserveAccount.SALARY.value, Currency.NZD, True)
        next_months_expenses: Decimal = Decimal("0")

        for fixed_expense in monthly_finances.fixed_expenses_need_list + monthly_finances.fixed_expenses_want_list:
            next_months_expenses = next_months_expenses + fixed_expense.amount

        for reserve in monthly_finances.reserve_need_list + monthly_finances.reserve_want_list:
            next_months_expenses = next_months_expenses + reserve.amount

        await nzd_account.transfer(reserve_account, next_months_expenses)

    @staticmethod
    async def _transfer_savings(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        await nzd_account.transfer(monthly_finances.settings.savings_account, nzd_account.balance, is_amount_in_from_currency=True)

    @staticmethod
    def _get_monthly_finances_temp_file_path(month: datetime.date) -> str:
        #   TODO: Integrate OneDrive API
        download_file_line: str = sirius.common.get_environmental_secret(EnvironmentalSecret.MONTHLY_FINANCES_EXCEL_FILE_LINK.value) + "&download=1"
        excel_file_path: str = sirius.common.download_file_from_url(download_file_line)
        new_excel_file_path: str = f"{excel_file_path}.xlsx"
        os.rename(excel_file_path, new_excel_file_path)
        return new_excel_file_path

    @staticmethod
    async def get_monthly_finances(month: datetime.date, wise_account: WiseAccount | None = None) -> "MonthlyFinances":
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        excel_file_path: str = MonthlyFinances._get_monthly_finances_temp_file_path(month)
        fixed_expenses_need_list, fixed_expenses_want_list = MonthlyFinances._get_fixed_expenses(excel_file_path)
        reserve_need_list, reserve_want_list = MonthlyFinances._get_reserve(excel_file_path, wise_account)

        monthly_finances: MonthlyFinances = MonthlyFinances(
            excel_file_path=excel_file_path,
            fixed_expenses_need_list=fixed_expenses_need_list,
            fixed_expenses_want_list=fixed_expenses_want_list,
            reserve_need_list=reserve_need_list,
            reserve_want_list=reserve_want_list,
            scheduled_transfer_list=MonthlyFinances._get_scheduled_transfer_list(excel_file_path, wise_account),
            settings=Settings.get(excel_file_path, wise_account),
            summary=Summary.get(excel_file_path)
        )

        if monthly_finances.settings.month != month:
            await Discord.notify(f"**Error in Organize Monthly Finances Job**\n"
                                 f"*Description*: Monthly Finances Excel file's month does not match with input month\n"
                                 f"*Expected month*: {month.strftime('%b, %Y')}\n"
                                 f"*Month in Excel file*: {monthly_finances.settings.month.strftime('%b, %Y')}")

            raise ClientException("Monthly Finances Excel file's month does not match with input month")
        return monthly_finances

    @staticmethod
    async def organize_finances_when_salary_received(month: datetime.date = None) -> Summary:
        month = common.get_first_date_of_next_month(datetime.date.today()) if month is None else month
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        monthly_finances: MonthlyFinances = await MonthlyFinances.get_monthly_finances(month, wise_account)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)

        if nzd_account.balance < monthly_finances.settings.salary:
            raise ClientException(f"Salary is not in account\n"
                                  f"Salary: {sirius.common.get_decimal_str(monthly_finances.settings.salary)}\n"
                                  f"Balance: {sirius.common.get_decimal_str(nzd_account.balance)}\n")

        await MonthlyFinances._transfer_scheduled_transfers(monthly_finances, wise_account)
        await MonthlyFinances._reserve_next_months_expenses(monthly_finances, wise_account)
        await MonthlyFinances._transfer_savings(monthly_finances, wise_account)

        return Summary.get(monthly_finances.excel_file_path)

    @staticmethod
    async def do_organize_finances_for_at_start_of_month() -> None:
        if common.is_last_day_of_month():
            await MonthlyFinances.organize_monthly_finances(common.get_first_date_of_next_month(datetime.date.today()))

    @staticmethod
    async def organize_monthly_finances(month: datetime.date) -> Summary:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        salary_reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(WiseReserveAccount.SALARY.value, Currency.NZD, True)
        monthly_finances: MonthlyFinances = await MonthlyFinances.get_monthly_finances(month, wise_account)

        if salary_reserve_account.balance < monthly_finances.summary.total_expenses:
            await Discord.notify(f"**Insufficient balance in Salary Reserve Account**\n"
                                 f"*Balance*: {salary_reserve_account.currency.value} {sirius.common.get_decimal_str(salary_reserve_account.balance)}\n"
                                 f"*Required Balance*: {salary_reserve_account.currency.value} {sirius.common.get_decimal_str(monthly_finances.summary.total_expenses)}\n"
                                 f"*Short of:* {salary_reserve_account.currency.value} {sirius.common.get_decimal_str(monthly_finances.summary.total_expenses - salary_reserve_account.balance)}")

            raise ClientException("Insufficient balance in Salary Reserve Account")

        await salary_reserve_account.transfer(nzd_account, monthly_finances.summary.total_expenses)
        await MonthlyFinances._transfer_reserves(monthly_finances, wise_account)
        await MonthlyFinances._transfer_fixed_expenses(monthly_finances, wise_account)

        return Summary.get(monthly_finances.excel_file_path)
