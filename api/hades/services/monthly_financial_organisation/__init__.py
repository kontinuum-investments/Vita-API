import datetime
import os
from decimal import Decimal
from typing import List, Tuple, Any, Dict

from sirius import common, excel
from sirius.common import DataClass, Currency
from sirius.wise import Account, WiseAccount, WiseAccountType, Recipient, CashAccount, ReserveAccount

import api.common
from api.athena.services.discord import Discord
from api.common import EnvironmentalSecret
from api.exceptions import ClientException


class Transfer(DataClass):
    description: str
    amount: Decimal
    recipient: Account | Recipient


class MonthlyFinances(DataClass):
    excel_file_path: str
    salary: Decimal
    needs: Decimal
    wants: Decimal
    needs_transfer_list: List[Transfer]
    wants_transfer_list: List[Transfer]
    savings: Transfer

    @staticmethod
    def get_monthly_finances(month: datetime.date | None = None, wise_account: WiseAccount | None = None) -> "MonthlyFinances":
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        month = datetime.date.today() if month is None else month
        excel_file_path: str = MonthlyFinances._get_monthly_finances_temp_file_path(month)
        needs_transfer_list, wants_transfer_list, savings = MonthlyFinances._get_transfers(excel_file_path, wise_account)

        return MonthlyFinances(
            excel_file_path=excel_file_path,
            salary=MonthlyFinances._get_salary(excel_file_path),
            needs=sum(transfer.amount for transfer in needs_transfer_list),
            wants=sum(transfer.amount for transfer in wants_transfer_list),
            needs_transfer_list=needs_transfer_list,
            wants_transfer_list=wants_transfer_list,
            savings=savings
        )

    @staticmethod
    async def do(month: datetime.date | None = None, wise_account: WiseAccount | None = None) -> "MonthlyFinances":
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        month = api.common.get_first_date_of_next_month(datetime.date.today()) if month is None else month
        monthly_finances: MonthlyFinances = MonthlyFinances.get_monthly_finances(month, wise_account)
        salary_reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account("Salary", Currency.NZD)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)

        if api.common.is_last_day_of_month() or common.is_development_environment():
            if salary_reserve_account.balance < monthly_finances.salary:
                await Discord.notify(f"**Insufficient balance in Salary Reserve Account**\n"
                                     f"*Balance*: {salary_reserve_account.currency.value} {common.get_decimal_str(salary_reserve_account.balance)}\n"
                                     f"*Required Balance*: {salary_reserve_account.currency.value} {common.get_decimal_str(monthly_finances.salary)}\n"
                                     f"*Short of:* {salary_reserve_account.currency.value} {common.get_decimal_str(monthly_finances.salary - salary_reserve_account.balance)}")

                raise ClientException("Insufficient balance in Salary Reserve Account")

            await nzd_account.transfer(monthly_finances.savings.recipient, monthly_finances.savings.amount, is_amount_in_from_currency=True)
            for transfer in monthly_finances.needs_transfer_list + monthly_finances.wants_transfer_list:
                await nzd_account.transfer(transfer.recipient, transfer.amount)

            await Discord.notify(f"**Monthly Finances**\n"
                                 f"*Needs*: {nzd_account.currency.value} {common.get_decimal_str(monthly_finances.needs)}\n"
                                 f"*Wants*: {nzd_account.currency.value} {common.get_decimal_str(monthly_finances.wants)}\n"
                                 f"*Savings*: {nzd_account.currency.value} {common.get_decimal_str(monthly_finances.savings.amount)}\n")

        return monthly_finances

    @staticmethod
    def _get_monthly_finances_temp_file_path(month: datetime.date) -> str:
        #   TODO: Integrate OneDrive API
        download_file_line: str = common.get_environmental_secret(EnvironmentalSecret.MONTHLY_FINANCES_EXCEL_FILE_LINK.value) + "&download=1"
        excel_file_path: str = common.download_file_from_url(download_file_line)
        new_excel_file_path: str = f"{excel_file_path}.xlsx"
        os.rename(excel_file_path, new_excel_file_path)
        return new_excel_file_path

    @staticmethod
    def _get_transfers(excel_file_path: str, wise_account: WiseAccount | None = None) -> Tuple[List[Transfer], List[Transfer], Transfer]:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        needs_transfer_list: List[Transfer] = []
        wants_transfer_list: List[Transfer] = []

        for sheet_name in ["Needs", "Wants"]:
            raw_transfers_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, sheet_name)
            for raw_transfer in raw_transfers_list:
                description: str = raw_transfer["Description"]
                currency: Currency = Currency(raw_transfer["Currency"])
                transfer: Transfer = Transfer(
                    description=raw_transfer["Description"],
                    amount=raw_transfer["Amount"],
                    recipient=wise_account.personal_profile.get_reserve_account(f"{description} ({sheet_name})", currency, True)
                )

                if "Needs" == sheet_name:
                    needs_transfer_list.append(transfer)
                elif "Wants" == sheet_name:
                    wants_transfer_list.append(transfer)

        raw_summary_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Summary")
        raw_summary: Dict[str, Any] = next(filter(lambda x: x["Description"] == "Total Savings", raw_summary_list))
        savings: Transfer = Transfer(
            description="Savings",
            amount=raw_summary["Amount"] + wise_account.personal_profile.get_cash_account(Currency.NZD).balance,
            recipient=MonthlyFinances._get_savings_recipient(excel_file_path, wise_account)
        )

        return needs_transfer_list, wants_transfer_list, savings

    @staticmethod
    def _get_savings_recipient(excel_file_path: str, wise_account: WiseAccount) -> Recipient:
        raw_setting_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Settings")
        raw_setting: Dict[str, Any] = next(filter(lambda x: x["Key"] == "Savings Account Number", raw_setting_list))
        account_number: str = raw_setting["Value"]
        return wise_account.personal_profile.get_recipient(account_number)

    @staticmethod
    def _get_salary(excel_file_path: str) -> Decimal:
        raw_setting_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Settings")
        raw_setting: Dict[str, Any] = next(filter(lambda x: x["Key"] == "Salary", raw_setting_list))
        return raw_setting["Value"]
