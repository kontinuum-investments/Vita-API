import asyncio
import json

from sirius import common
from sirius.communication import discord
from sirius.communication.logger import Logger
from sirius.wise import AccountCredit, AccountDebit, WiseWebhook, WiseAccount, WiseAccountType
from starlette.requests import Request

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.models.database import WiseAccountUpdate
from api.hades.services.organize_monthly_finances import MonthlyFinances
from api.hades.services.organize_rent import Tenant


class WisePrimaryCreditEvent:
    @staticmethod
    async def do(account_credit: AccountCredit) -> None:
        if "chelmer" in account_credit.transaction.third_party:
            await MonthlyFinances.organize_finances_when_salary_received()


class WiseSecondaryCreditEvent:
    @staticmethod
    async def do(account_credit: AccountCredit) -> None:
        await Tenant.process_incoming_transfer(account_credit.transaction)


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
            message: str = f"**{wise_account_type_name} Account Update**:\n" \
                           f"*Description*: Account Debited\n" \
                           f"*Account*: {account_update.account.currency.value}\n" \
                           f"*Balance*: {account_update.account.currency.value} {common.get_decimal_str(account_update.account_balance)}\n" \
                           f"*Timestamp*: {discord.get_timestamp_string(account_update.timestamp)}"

            if account_update.transaction is not None:
                asyncio.ensure_future(WisePrimaryCreditEvent.do(account_update) if WiseAccountType.PRIMARY == wise_account_type else WiseSecondaryCreditEvent.do(account_update))
                message = message + f"\n*From*: {account_update.transaction.third_party}\n" \
                                    f"*Credited Amount*: {account_update.account.currency.value} {common.get_decimal_str(account_update.transaction.amount)}\n"

            await Discord.send_message(DiscordTextChannel.WISE, message)

        await WiseAccountUpdate(wise_delivery_id=wise_delivery_id).save()
