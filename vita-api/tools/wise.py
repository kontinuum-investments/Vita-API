import asyncio
from decimal import Decimal
from typing import List

from fastapi import APIRouter
from sirius.common import Currency, DataClass
from sirius.wise import WiseAccount, Account, Transaction

router = APIRouter()
_wise_account: WiseAccount | None = None
_wise_account_lock = asyncio.Lock()


class WiseAccountSummaryResponse(DataClass):
    account_name: str
    currency: Currency
    balance: Decimal


class WiseTransaction(DataClass):
    description: str
    currency: Currency
    amount: Decimal


async def get_wise_account() -> WiseAccount:
    global _wise_account
    if _wise_account is None:
        async with _wise_account_lock:
            if _wise_account is None:
                _wise_account = await WiseAccount.get()

    return _wise_account


@router.get("/latest_transactions", summary="Fetches the most recent transactions from a specific currency's Wise account.")
async def get_latest_transactions(currency_str: str | None = None) -> List[WiseTransaction]:
    currency: Currency = Currency.NZD if currency_str is None else Currency(currency_str)
    wise_account: WiseAccount = await get_wise_account()
    account_list: List[Account] = await wise_account.personal_profile.account_list
    account: Account = next(filter(lambda a: a.currency == currency, account_list))
    transaction_list: List[Transaction] = await account.get_transactions(number_of_past_hours=24)

    return [WiseTransaction(description=transaction.description, currency=currency, amount=transaction.amount) for transaction in transaction_list]


@router.get("/account_summary", summary="Provides a summary of all Wise cash and reserve accounts.")
async def get_account_summary() -> List[WiseAccountSummaryResponse]:
    wise_account: WiseAccount = await get_wise_account()
    account_list: List[Account] = await wise_account.personal_profile.account_list

    return [WiseAccountSummaryResponse(account_name=account.name, currency=account.currency, balance=account.balance) for account in account_list]
