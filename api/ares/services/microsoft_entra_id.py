from enum import Enum
from typing import List

from sirius.communication.discord import TextChannel
from sirius.iam.microsoft_entra_id import MicrosoftIdentityToken

from api.common import DiscordTextChannel


class Scope(Enum):
    USER_READ: str = "User.Read"


class MicrosoftEntraID:

    @staticmethod
    async def get_access_token(application_name: str, scope_list: List[Scope]) -> MicrosoftIdentityToken:
        notification_text_channel: TextChannel = await TextChannel.get_text_channel_from_default_bot_and_server(DiscordTextChannel.NOTIFICATION.value)
        return await MicrosoftIdentityToken.get_token([s.value for s in scope_list], notification_text_channel, application_name)

    @staticmethod
    async def is_access_token_valid(access_token: str) -> bool:
        return await MicrosoftIdentityToken.is_access_token_valid(access_token)
