import datetime
from decimal import Decimal
from typing import List, Any, Dict

from sirius import common, excel
from sirius.common import DataClass, Currency
from sirius.wise import WiseAccount, WiseAccountType, CashAccount, ReserveAccount

import api.common
from api.athena.services.discord import Discord
from api.exceptions import ClientException
from api.hades.common import FinancesSettings, PlannedExpense


class MonthlyFinances(DataClass):
    excel_file_path: str
    salary: Decimal
    needs: Decimal
    wants: Decimal
    needs_planned_expense_list: List[PlannedExpense]
    wants_planned_expense_list: List[PlannedExpense]
    scheduled_planned_expense_list: List[PlannedExpense]
    savings: PlannedExpense

    @staticmethod
    def get_monthly_finances(wise_account: WiseAccount | None = None) -> "MonthlyFinances":
        excel_file_path: str = FinancesSettings.get_monthly_finances_excel_file_path()
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        needs_planned_expense_list, wants_planned_expense_list, scheduled_planned_expense_list, savings = PlannedExpense.get_all(wise_account)

        return MonthlyFinances(
            excel_file_path=excel_file_path,
            salary=MonthlyFinances.get_salary(excel_file_path),
            needs=sum(planned_expense.amount for planned_expense in needs_planned_expense_list),
            wants=sum(planned_expense.amount for planned_expense in wants_planned_expense_list),
            needs_planned_expense_list=needs_planned_expense_list,
            wants_planned_expense_list=wants_planned_expense_list,
            scheduled_planned_expense_list=scheduled_planned_expense_list,
            savings=savings
        )

    @staticmethod
    async def do(wise_account: WiseAccount | None = None) -> "MonthlyFinances":
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        monthly_finances: MonthlyFinances = MonthlyFinances.get_monthly_finances(wise_account)
        salary_reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account("Salary", Currency.NZD)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)

        if api.common.is_last_day_of_month() or common.is_development_environment():
            if salary_reserve_account.balance < monthly_finances.salary:
                await Discord.notify(f"**Insufficient balance in Salary Reserve Account**\n"
                                     f"*Balance*: {salary_reserve_account.currency.value} {common.get_decimal_str(salary_reserve_account.balance)}\n"
                                     f"*Required Balance*: {salary_reserve_account.currency.value} {common.get_decimal_str(monthly_finances.salary)}\n"
                                     f"*Short of:* {salary_reserve_account.currency.value} {common.get_decimal_str(monthly_finances.salary - salary_reserve_account.balance)}")

                raise ClientException("Insufficient balance in Salary Reserve Account")

            [await nzd_account.transfer(transfer.recipient, transfer.amount) for transfer in monthly_finances.needs_planned_expense_list + monthly_finances.wants_planned_expense_list]
            [PlannedExpense.do_scheduled_planned_expense(scheduled_transfer) for scheduled_transfer in monthly_finances.scheduled_planned_expense_list]
            await nzd_account.transfer(monthly_finances.savings.recipient, nzd_account.balance, is_amount_in_from_currency=True)

            await Discord.notify(f"**Monthly Finances**\n"
                                 f"*Needs*: {nzd_account.currency.value} {common.get_decimal_str(monthly_finances.needs)}\n"
                                 f"*Wants*: {nzd_account.currency.value} {common.get_decimal_str(monthly_finances.wants)}\n"
                                 f"*Savings*: {nzd_account.currency.value} {common.get_decimal_str(monthly_finances.savings.amount)}\n")

        return monthly_finances

    @staticmethod
    def get_salary(excel_file_path: str | None = None) -> Decimal:
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path
        raw_setting_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Settings")
        raw_setting: Dict[str, Any] = next(filter(lambda x: x["Key"] == "Salary", raw_setting_list))
        return raw_setting["Value"]
