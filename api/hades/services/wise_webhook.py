from typing import Any, Dict

from sirius.wise import AccountCredit, AccountDebit, WiseWebhook


class AccountUpdate:

    @classmethod
    async def handle_balance_update(cls, request_data: Dict[str, Any]) -> None:
        account_update: AccountDebit | AccountCredit | None = await WiseWebhook.get_balance_update_object(request_data)
