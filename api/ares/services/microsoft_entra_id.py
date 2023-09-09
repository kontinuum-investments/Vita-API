from fastapi import Request
from sirius import common
from sirius.communication.discord import TextChannel
from sirius.constants import EnvironmentVariable
from sirius.iam.exceptions import InvalidAccessTokenException, AccessTokenRetrievalTimeoutException
from sirius.iam.microsoft_entra_id import MicrosoftIdentityToken, MicrosoftIdentity

from api.athena.constants import DiscordTextChannel
from api.exceptions import ClientException


class MicrosoftEntraID:

    @staticmethod
    async def get_access_token(application_name: str, entra_id_client_id: str | None = None) -> MicrosoftIdentityToken:
        entra_id_client_id = common.get_environmental_variable(EnvironmentVariable.ENTRA_ID_CLIENT_ID) if entra_id_client_id is None else entra_id_client_id
        notification_text_channel: TextChannel = await TextChannel.get_text_channel_from_default_bot_and_server(DiscordTextChannel.NOTIFICATION.value)
        return await MicrosoftIdentity.get_token([f"{entra_id_client_id}/.default"], notification_text_channel, application_name)

    @staticmethod
    async def get_identity_from_request(request: Request, entra_id_client_id: str | None = None, entra_id_tenant_id: str | None = None) -> "MicrosoftIdentity":
        entra_id_client_id = common.get_environmental_variable(EnvironmentVariable.ENTRA_ID_CLIENT_ID) if entra_id_client_id is None else entra_id_client_id
        entra_id_tenant_id = common.get_environmental_variable(EnvironmentVariable.ENTRA_ID_TENANT_ID) if entra_id_tenant_id is None else entra_id_tenant_id

        if request.headers.get("authorization") is None or "Bearer " not in request.headers.get("authorization"):
            raise InvalidAccessTokenException("Invalid Token in Header")

        access_token = request.headers.get("authorization").replace("Bearer ", "")

        try:
            microsoft_identity: MicrosoftIdentity = await MicrosoftIdentity.get_identity_from_access_token(access_token, entra_id_client_id, entra_id_tenant_id)
        except InvalidAccessTokenException:
            raise ClientException("Invalid Access Token")
        except AccessTokenRetrievalTimeoutException:
            raise ClientException("Login timed-out")

        microsoft_identity.ip_address = request.client.host
        microsoft_identity.port_number = request.client.port
        return microsoft_identity
