from typing import Annotated

import sirius.common
from fastapi import APIRouter, Depends, Request
from sirius.iam import Identity
from sirius.iam.microsoft_entra_id import MicrosoftEntraIDAuthenticationIDStore

from api.ares import constants
from api.ares.models.http import ConnectionInfo
from api.ares.services.microsoft_entra_id import MicrosoftEntraID
from api.constants import ROUTE__ARES

ares_router = APIRouter(prefix=ROUTE__ARES)


async def get_identity(request: Request) -> Identity:
    return Identity.get_identity_from_request(request)


@ares_router.post(constants.ROUTE__GET_ACCESS_TOKEN_REMOTELY)
async def get_access_token_remotely(request: Request) -> str:
    redirect_url: str = request.get("redirect_url")
    return await Identity.get_access_token_remotely(constants.MICROSOFT_ENTRA_ID_DEFAULT_AUTHENTICATION_REDIRECT_URL if redirect_url is None else redirect_url, request.get("client")[0], request.get("client")[1])


@ares_router.get(constants.ROUTE__ENTRA_ID_LOGIN_URL)
async def get_entra_id_login_url(redirect_url: str | None = None) -> str:
    return MicrosoftEntraID.get_login_url(redirect_url)


@ares_router.get(constants.ROUTE__ENTRA_ID_RESPONSE, include_in_schema=False)
async def entra_id_response(state: str, code: str) -> None:
    MicrosoftEntraIDAuthenticationIDStore.add(state, code)


@ares_router.get(constants.ROUTE__GET_CURRENT_USER)
async def get_current_user(identity: Annotated[Identity, Depends(get_identity)]) -> Identity:
    return identity


@ares_router.get(constants.ROUTE__GET_CONNECTION_INFO)
async def get_connection_data(request: Request) -> ConnectionInfo:
    return ConnectionInfo(client_ip=request.get("client")[0],
                          client_port=request.get("client")[1],
                          server_fqdn=sirius.common.get_servers_fqdn())
