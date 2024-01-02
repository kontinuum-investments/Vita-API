import datetime
import os
from decimal import Decimal
from typing import Dict, Any

from sirius import common, excel
from sirius.common import Currency
from sirius.wise import WiseAccount, WiseAccountType, CashAccount

from api.athena.services.discord import Discord
from api.common import EnvironmentalSecret
from api.exceptions import ClientException


class FinancesSettings:

    @staticmethod
    def get_monthly_finances_excel_file_path(month: datetime.date | None = None) -> str:
        #   TODO: Integrate OneDrive API
        month: datetime.date = datetime.date.today() if month is None else month
        download_file_line: str = common.get_environmental_secret(EnvironmentalSecret.MONTHLY_FINANCES_EXCEL_FILE_LINK.value) + "&download=1"
        excel_file_path: str = common.download_file_from_url(download_file_line)
        new_excel_file_path: str = f"{excel_file_path}.xlsx"
        os.rename(excel_file_path, new_excel_file_path)
        return new_excel_file_path

    @staticmethod
    def get_settings() -> Dict[str, Any]:
        settings: Dict[str, Any] = {}
        for raw_setting in excel.get_excel_data(FinancesSettings.get_monthly_finances_excel_file_path(None), "Settings"):
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
            Discord.notify_error("Validating Cash Reserve", f"*Expected Amount*: {nzd_account.currency.value}{common.get_decimal_str(cash_reserve_amount)}\n"
                                                            f"*Actual Amount*: {nzd_account.currency.value}{common.get_decimal_str(nzd_account.balance)}")
