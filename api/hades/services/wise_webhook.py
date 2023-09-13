import json

from sirius import common
from sirius.communication import discord
from sirius.communication.logger import Logger
from sirius.wise import AccountCredit, AccountDebit, WiseWebhook, WiseAccount, WiseAccountType
from starlette.requests import Request

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.models.database import WiseAccountUpdate


class AccountUpdate:

    @classmethod
    async def handle_account_update(cls, request: Request, wise_account_type: WiseAccountType) -> None:
        wise_account_type_name: str = "Primary" if wise_account_type == WiseAccountType.PRIMARY else "Secondary"
        wise_delivery_id: str = request.headers["X-Delivery-Id"]
        request_data = await request.json()
        if await WiseAccountUpdate.is_duplicate(wise_delivery_id):
            await Logger.debug(f"Duplicate {wise_account_type_name.lower()} account update received:\n{json.dumps(request_data)}")

        if request_data["data"]["resource"]["id"] == 0:
            await Logger.notify(f"Wise Webhook set up successfully for {wise_account_type_name} Account")

        wise_account: WiseAccount = WiseAccount.get(wise_account_type)
        try:
            account_update: AccountDebit | AccountCredit | None = await WiseWebhook.get_balance_update_object(request_data, wise_account)
        except Exception:
            await Logger.debug(f"Un-parsable {wise_account_type_name} account update received:\n{json.dumps(request_data)}")
            return

        if isinstance(account_update, AccountCredit):
            await Discord.send_message(DiscordTextChannel.WISE, f"**{wise_account_type_name} Account Update**:\n"
                                                                f"*Description*: Account Debited\n"
                                                                f"*Account*: {account_update.account.currency.value}\n"
                                                                f"*From*: {account_update.transaction.third_party}\n"
                                                                f"*Credited Amount*: {account_update.account.currency.value} {common.get_decimal_str(account_update.transaction.amount)}\n"
                                                                f"*Balance*: {account_update.account.currency.value} {common.get_decimal_str(account_update.account_balance)}\n"
                                                                f"*Timestamp*: {discord.get_timestamp_string(account_update.timestamp)}")

        await WiseAccountUpdate(wise_delivery_id=wise_delivery_id).save()
