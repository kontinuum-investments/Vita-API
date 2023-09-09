from _decimal import Decimal
from sirius.common import get_decimal_str
from sirius.communication.discord import get_timestamp_string
from sirius.wise import WebhookAccountUpdateType

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.models import http
from api.hades.models.http import BalanceUpdateType


class AccountUpdate:

    @classmethod
    async def handle_balance_update(cls, wise_web_hook: http.WiseWebHook) -> None:
        message_header: str = "**__Wise Account Update__**\n"

        await Discord.send_message(DiscordTextChannel.WISE, message_header + str(wise_web_hook))

        # if wise_web_hook.event_type == WebhookAccountUpdateType.UPDATE:
        #     amount: Decimal = wise_web_hook.data.amount if wise_web_hook.data.transaction_type == BalanceUpdateType.CREDIT else (wise_web_hook.data.amount * Decimal("-1"))
        #     await Discord.send_message(DiscordTextChannel.WISE, message_header +
        #                                f"Event: Funds Moved\n"
        #                                f"Timestamp: {get_timestamp_string(wise_web_hook.data.occurred_at)}\n"
        #                                f"Account: {wise_web_hook.data.name}\n"
        #                                f"Amount: {wise_web_hook.data.currency.value} {get_decimal_str(amount)}\n"
        #                                f"Reference: {wise_web_hook.data.transfer_reference}")
