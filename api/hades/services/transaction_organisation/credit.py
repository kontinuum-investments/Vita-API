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
        from api.hades.services.transaction_organisation import ExpectedRemitter

        expected_remitter: ExpectedRemitter | None = ExpectedRemitter.get(transaction)
        await transaction.account.transfer(expected_remitter.reserve_account, transaction.amount)
        if expected_remitter.notification_phone_number is not None:
            asyncio.ensure_future(sms.send_message(expected_remitter.notification_phone_number,
                                                   f"A fund transfer of {transaction.account.currency.value} {common.get_decimal_str(transaction.transaction.amount)} has been "
                                                   f"received.\nThis is an automated message from Athena."))

        asyncio.ensure_future(Discord.send_message(DiscordTextChannel.WISE, f"**Account Credited**\n"
                                                                            f"*From*: {transaction.transaction.third_party if expected_remitter.is_unknown_recipient else expected_remitter.recipient_name}\n"
                                                                            f"*Amount*: {transaction.account.currency.value} {common.get_decimal_str(transaction.transaction.amount)}\n"
                                                                            f"*Reserve Account Balance*: {transaction.account.currency.value} {common.get_decimal_str(expected_remitter.reserve_account.balance)}"))

        FinancesSettings.notify_if_only_cash_reserve_amount_present(transaction.account.profile.wise_account)
