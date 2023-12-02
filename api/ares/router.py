from typing import Annotated

import sirius.common
from fastapi import APIRouter, Depends, Request
from sirius.iam.microsoft_entra_id import MicrosoftIdentity, MicrosoftEntraIDAuthenticationIDStore

from api.ares import constants
from api.ares.models.http import ConnectionInfo
from api.ares.services.microsoft_entra_id import MicrosoftEntraID
from api.constants import ROUTE__ARES

ares_router = APIRouter(prefix=ROUTE__ARES)


async def get_microsoft_identity(request: Request) -> MicrosoftIdentity:
    return await MicrosoftEntraID.get_identity_from_request(request)


@ares_router.post(constants.ROUTE__GET_ACCESS_TOKEN_REMOTELY)
async def get_access_token_remotely() -> str:
    return await MicrosoftEntraID.get_access_token_remotely()


@ares_router.get(constants.ROUTE__ENTRA_ID_LOGIN_URL)
async def get_entra_id_login_url(redirect_url: str | None = None) -> str:
    return MicrosoftEntraID.get_login_url(redirect_url)


@ares_router.get(constants.ROUTE__ENTRA_ID_RESPONSE, include_in_schema=False)
async def entra_id_response(state: str, code: str) -> None:
    MicrosoftEntraIDAuthenticationIDStore.add(state, code)


@ares_router.get(constants.ROUTE__GET_CURRENT_USER)
async def get_current_user(microsoft_identity: Annotated[MicrosoftIdentity, Depends(get_microsoft_identity)]) -> MicrosoftIdentity:
    return microsoft_identity


@ares_router.get(constants.ROUTE__GET_CONNECTION_INFO)
async def get_connection_data(request: Request) -> ConnectionInfo:
    return ConnectionInfo(client_ip=request.get("client")[0],
                          client_port=request.get("client")[1],
                          server_fqdn=sirius.common.get_servers_fqdn())
