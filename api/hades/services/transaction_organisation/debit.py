import datetime
from decimal import Decimal
from typing import List

from sirius.common import Currency
from sirius.wise import WiseAccount, WiseAccountType, CashAccount, Transaction, TransactionType, Recipient

from api.hades.common import FinancesSettings, PlannedExpense


class WiseDebitEvent:
    @staticmethod
    async def organise_transactions(from_time: datetime.datetime | None = None, wise_account: WiseAccount | None = None) -> None:
        from_time = datetime.datetime.now() - datetime.timedelta(hours=1) if from_time is None else from_time
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        transaction_list: List[Transaction] = list(filter(lambda t: t.type == TransactionType.CARD, nzd_account.get_transactions(from_time)))
        excel_file_path: str = FinancesSettings.get_monthly_finances_excel_file_path()

        [await WiseDebitEvent.do(transaction, excel_file_path) for transaction in transaction_list]  # type: ignore[func-returns-value]
        FinancesSettings.notify_if_only_cash_reserve_amount_present(wise_account)

    @staticmethod
    async def do(transaction: Transaction, excel_file_path: str | None = None) -> None:
        from api.hades.services.transaction_organisation import SharedExpense

        if isinstance(transaction.third_party, str):
            third_party_name: str = transaction.third_party.split(" | ")[0]
        elif isinstance(transaction.third_party, Recipient):
            third_party_name = transaction.third_party.account_holder_name
        else:
            return

        wise_account: WiseAccount = transaction.account.profile.wise_account
        excel_file_path = FinancesSettings.get_monthly_finances_excel_file_path() if excel_file_path is None else excel_file_path
        planned_expense: PlannedExpense | None = PlannedExpense.get_by_merchant_name(third_party_name, wise_account, excel_file_path)
        shared_expense: SharedExpense | None = SharedExpense.get_by_merchant_name(third_party_name, wise_account, excel_file_path)

        if shared_expense is not None:
            await shared_expense.do_planned_shared_expense(transaction, planned_expense)
        elif planned_expense is not None:
            await planned_expense.do_planned_expense(transaction.amount * Decimal("-1"))
        else:
            await FinancesSettings.top_up_cash_reserve_from_daily_expense_reserve_account(wise_account, transaction.amount * Decimal("-1"))
