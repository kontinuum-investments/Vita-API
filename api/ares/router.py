from typing import Annotated
from urllib.parse import urlparse

import sirius.common
from fastapi import APIRouter, Depends, Request, Response
from sirius import common
from sirius.iam import Identity
from sirius.iam.microsoft_entra_id import MicrosoftEntraIDAuthenticationIDStore
from starlette.responses import JSONResponse

from api.ares import constants
from api.ares.models.http import ConnectionInfo
from api.ares.services.microsoft_entra_id import MicrosoftEntraID
from api.athena.services.url_shortner import URLStore
from api.constants import ROUTE__ARES, BASE_URL

ares_router = APIRouter(prefix=ROUTE__ARES)


async def get_identity(request: Request) -> Identity | None:
    if common.is_ci_cd_pipeline_environment():
        return None

    return Identity.get_identity_from_request(request)


@ares_router.post(constants.ROUTE__GET_ACCESS_TOKEN_REMOTELY)
async def get_access_token_remotely(request: Request) -> Response:
    redirect_url: str = request.get("redirect_url") if "redirect_url" in request else constants.MICROSOFT_ENTRA_ID_DEFAULT_AUTHENTICATION_REDIRECT_URL
    access_token: str = await Identity.get_access_token_remotely(redirect_url,
                                                                 request.get("client")[0],
                                                                 request.get("client")[1],
                                                                 url_shortener_function=lambda u: URLStore.get_shortened_url(url=u))

    response = JSONResponse({"access_token": access_token})
    response.headers["Authorization"] = f"Bearer {access_token}"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        secure=True,
        httponly=True,
        domain=urlparse(BASE_URL).netloc.split(':')[0]
    )

    return response


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
