from typing import List

from sirius.common import Currency
from sirius.wise import WiseAccount, Account, Transaction

import asyncio

_wise_account: WiseAccount | None = None
_wise_account_lock = asyncio.Lock()


async def get_wise_account() -> WiseAccount:
    global _wise_account
    if _wise_account is None:
        async with _wise_account_lock:
            if _wise_account is None:
                _wise_account = await WiseAccount.get()

    return _wise_account


async def get_latest_wise_transactions(currency_str: str | None = None) -> str:
    currency: Currency = Currency.NZD if currency_str is None else Currency(currency_str)
    wise_account: WiseAccount = await get_wise_account()
    account_list: List[Account] = await wise_account.personal_profile.account_list
    account: Account = next(filter(lambda a: a.currency == currency, account_list))
    transaction_list: List[Transaction] = await account.get_transactions(number_of_past_hours=24)

    replies = [
        f"Transaction Description: {transaction.description}\nTransaction Amount (in {currency}): ${transaction.amount}"
        for transaction in transaction_list
    ]

    return '\n---\n'.join(replies)


async def get_wise_account_summary() -> str:
    replies: List[str] = []
    wise_account: WiseAccount = await get_wise_account()
    account_list: List[Account] = await wise_account.personal_profile.account_list

    [replies.append(f"Account: {account.name}\nAccount Balance: {account.currency.value}{account.balance}") for account in account_list]  # type: ignore[func-returns-value]

    return '\n---\n'.join(replies)
