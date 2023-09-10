from typing import Any, Dict

from sirius import common
from sirius.communication import discord
from sirius.wise import AccountCredit, AccountDebit, WiseWebhook, WiseAccount, WiseAccountType

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.models.database import WiseAccountUpdate


class AccountUpdate:

    @classmethod
    async def primary_account_update(cls, request_data: Dict[str, Any]) -> None:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        account_update: AccountDebit | AccountCredit | None = await WiseWebhook.get_balance_update_object(request_data, wise_account)
        if WiseAccountUpdate.is_duplicate(wise_account.type, account_update):
            return

        await WiseAccountUpdate.save_to_database(WiseAccountType.SECONDARY, account_update)
        if isinstance(account_update, AccountDebit):
            await Discord.send_message(DiscordTextChannel.WISE, f"**Primary Account Update**:\n"
                                                                f"*Description*: Account Credited\n"
                                                                f"*Timestamp*: {discord.get_timestamp_string(account_update.timestamp)}")

        elif isinstance(account_update, AccountDebit) and account_update.is_successful:
            await Discord.send_message(DiscordTextChannel.WISE, f"**Primary Account Update**:\n"
                                                                f"*Description*: Account Debited\n"
                                                                f"*Account*: {account_update.account.currency.value}\n"
                                                                f"*From*: {account_update.transaction.third_party}\n"
                                                                f"*Credited Amount*: {account_update.account.currency.value} {common.get_decimal_str(account_update.transaction.amount)}\n"
                                                                f"*Balance*: {account_update.account.currency.value} {common.get_decimal_str(account_update.account_balance)}\n"
                                                                f"*Timestamp*: {discord.get_timestamp_string(account_update.timestamp)}")

        await WiseAccountUpdate.save_to_database(WiseAccountType.PRIMARY, account_update)

    @classmethod
    async def secondary_account_update(cls, request_data: Dict[str, Any]) -> None:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.SECONDARY)
        account_update: AccountDebit | AccountCredit | None = await WiseWebhook.get_balance_update_object(request_data, wise_account)
        if WiseAccountUpdate.is_duplicate(wise_account.type, account_update):
            return

        await WiseAccountUpdate.save_to_database(WiseAccountType.SECONDARY, account_update)
        if isinstance(account_update, AccountDebit):
            await Discord.send_message(DiscordTextChannel.WISE, f"**Secondary Account Update**:\n"
                                                                f"*Description*: Account Credited\n"
                                                                f"*Timestamp*: {discord.get_timestamp_string(account_update.timestamp)}")

        elif isinstance(account_update, AccountDebit) and account_update.is_successful:
            await Discord.send_message(DiscordTextChannel.WISE, f"**Secondary Account Update**:\n"
                                                                f"*Description*: Account Debited\n"
                                                                f"*Account*: {account_update.account.currency.value}\n"
                                                                f"*From*: {account_update.transaction.third_party}\n"
                                                                f"*Credited Amount*: {account_update.account.currency.value} {common.get_decimal_str(account_update.transaction.amount)}\n"
                                                                f"*Balance*: {account_update.account.currency.value} {common.get_decimal_str(account_update.account_balance)}\n"
                                                                f"*Timestamp*: {discord.get_timestamp_string(account_update.timestamp)}")
