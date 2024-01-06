import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING

from sirius.common import Currency
from sirius.wise import WiseAccount, WiseAccountType, CashAccount, Transaction, AccountDebit

from api.hades.common import FinancesSettings

if TYPE_CHECKING:
    from api.hades.services.transaction_organisation import ExpectedRemitter


class WiseDebitEvent:
    @staticmethod
    async def organise_transactions(from_time: datetime.datetime | None = None, wise_account: WiseAccount | None = None) -> None:
        from_time = datetime.datetime.now() - datetime.timedelta(hours=1) if from_time is None else from_time
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        transaction_list: List[Transaction] = list(filter(lambda t: isinstance(t.third_party, str) and t.amount < Decimal("0"), nzd_account.get_transactions(from_time)))

        [await WiseDebitEvent.do(AccountDebit(wise_id=1,  # type: ignore[func-returns-value]
                                              is_attempted=False,
                                              is_successful=True,
                                              timestamp=transaction.timestamp,
                                              transaction=transaction)) for transaction in transaction_list]

    @staticmethod
    async def do(transaction: Transaction) -> None:
        expected_remitter: ExpectedRemitter | None = ExpectedRemitter.get_by_name_in_statement(transaction.third_party,
                                                                                               transaction.account.profile.wise_account) if isinstance(transaction.third_party, str) else None

        if expected_remitter is None:
            await FinancesSettings.top_up_cash_reserve_from_daily_expense_reserve_account(transaction.account.profile.wise_account)
        else:
            if WiseDebitEvent._is_shared_expense(transaction):
                await WiseDebitEvent._do_planned_shared_expense(transaction, expected_remitter)
            else:
                await WiseDebitEvent._do_planned_personal_expense(transaction, expected_remitter)

        FinancesSettings.notify_if_only_cash_reserve_amount_present(transaction.account.profile.wise_account)

    @staticmethod
    def _is_shared_expense(transaction: Transaction) -> bool:
        # TODO
        pass

    @staticmethod
    async def _do_planned_shared_expense(transaction: Transaction, expected_remitter: "ExpectedRemitter") -> None:
        # TODO
        # Withdraw half from reserve account

        # if third party's reserve account.balance < expense amount
        # Withdraw all from account balance
        # Withdraw remaining from Daily Expenses
        # Notify
        # else
        # Withdraw half from third party's reserve account
        pass

    @staticmethod
    async def _do_planned_personal_expense(transaction: Transaction, expected_remitter: "ExpectedRemitter") -> None:
        # TODO
        pass
