from enum import Enum

from sirius import common
from sirius.communication.discord import TextChannel
from sirius.constants import EnvironmentVariable
from sirius.iam.microsoft_entra_id import MicrosoftIdentityToken

from api.common import DiscordTextChannel


class Scope(Enum):
    USER_READ: str = "User.Read"


class MicrosoftEntraID:

    @staticmethod
    async def get_access_token(application_name: str, entra_id_client_id: str | None = None) -> MicrosoftIdentityToken:
        entra_id_client_id = common.get_environmental_variable(EnvironmentVariable.ENTRA_ID_CLIENT_ID) if entra_id_client_id is None else entra_id_client_id
        notification_text_channel: TextChannel = await TextChannel.get_text_channel_from_default_bot_and_server(DiscordTextChannel.NOTIFICATION.value)
        return await MicrosoftIdentityToken.get_token([f"{entra_id_client_id}/.default"], notification_text_channel, application_name)

    @staticmethod
    async def is_access_token_valid(access_token: str) -> bool:
        return await MicrosoftIdentityToken.is_access_token_valid(access_token)
