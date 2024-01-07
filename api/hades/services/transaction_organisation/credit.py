import asyncio

from sirius import common
from sirius.communication import sms
from sirius.wise import AccountCredit, Transaction

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.common import FinancesSettings


class WiseCreditEvent:

    @staticmethod
    async def do(transaction: Transaction) -> None:
        from api.hades.services.transaction_organisation import SharedExpense

        shared_expense: SharedExpense | None = SharedExpense.get(transaction)
        await transaction.account.transfer(shared_expense.reserve_account, transaction.amount)

        if shared_expense.notification_phone_number is not None:
            asyncio.ensure_future(sms.send_message(shared_expense.notification_phone_number,
                                                   f"A fund transfer of {transaction.account.currency.value} {common.get_decimal_str(transaction.transaction.amount)} has been "
                                                   f"received.\nThis is an automated message from Athena."))

        asyncio.ensure_future(Discord.send_message(DiscordTextChannel.WISE, f"**Account Credited**\n"
                                                                            f"*From*: {transaction.transaction.third_party if shared_expense.is_unknown_recipient else shared_expense.recipient_name}\n"
                                                                            f"*Amount*: {transaction.account.currency.value} {common.get_decimal_str(transaction.transaction.amount)}\n"
                                                                            f"*Reserve Account Balance*: {transaction.account.currency.value} {common.get_decimal_str(shared_expense.reserve_account.balance)}"))
