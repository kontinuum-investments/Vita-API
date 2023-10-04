from fastapi import Request
from sirius import common
from sirius.iam.microsoft_entra_id import MicrosoftIdentity

from api.ares import constants


class MicrosoftEntraID:

    @staticmethod
    async def get_identity_from_request(request: Request, entra_id_client_id: str | None = None, entra_id_tenant_id: str | None = None) -> "MicrosoftIdentity":
        return await MicrosoftIdentity.get_identity_from_request(request, entra_id_client_id, entra_id_tenant_id)

    @staticmethod
    def get_login_url(authentication_id: str | None = None, entra_id_tenant_id: str | None = None, entra_id_client_id: str | None = None, scope: str | None = None, redirect_url: str | None = None) -> str:
        authentication_id = common.get_unique_id() if authentication_id is None else authentication_id
        redirect_url = constants.MICROSOFT_ENTRA_ID_DEFAULT_AUTHENTICATION_REDIRECT_URL if redirect_url is None else redirect_url
        return MicrosoftIdentity.get_login_url(redirect_url, authentication_id, entra_id_tenant_id, entra_id_client_id, scope)

    @staticmethod
    async def get_access_token_remotely() -> str:
        return await MicrosoftIdentity.get_access_token_remotely(constants.MICROSOFT_ENTRA_ID_DEFAULT_AUTHENTICATION_REDIRECT_URL)
