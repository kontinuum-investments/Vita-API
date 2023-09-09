from typing import Any, Dict

from sirius.communication.discord import get_timestamp_string

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.models import AccountCredit


class AccountUpdate:

    @classmethod
    async def handle_balance_update(cls, request_data: Dict[str, Any]) -> None:
        message_header: str = "**__Wise Account Update__**\n"
        if request_data["event_type"] == "transfers#state-change":
            account_credit: AccountCredit = AccountCredit.get_from_request_data(request_data)
            await Discord.send_message(DiscordTextChannel.WISE, f"{message_header}"
                                                                f"Event: Account Credited\n"
                                                                f"Timestamp: {get_timestamp_string(account_credit.timestamp)}")
