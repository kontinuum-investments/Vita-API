from typing import List

from sirius.common import Currency
from sirius.wise import WiseAccount, WiseAccountType, Transaction

from api.hades.services.organize_monthly_finances import MonthlyFinances


class OrganizePrimaryAccountTransactions:

    @staticmethod
    async def do() -> None:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        transaction_list: List[Transaction] = wise_account.personal_profile.get_cash_account(Currency.NZD).get_transactions(number_of_past_hours=1)

        for transaction in transaction_list:
            if isinstance(transaction.third_party, str) and "chelmer" in transaction.third_party:
                await MonthlyFinances.organize_finances_when_salary_received()
