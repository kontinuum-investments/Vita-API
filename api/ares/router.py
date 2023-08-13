from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sirius.iam.microsoft_entra_id import MicrosoftIdentityToken, MicrosoftIdentity

from api.ares import constants
from api.ares.models import http
from api.ares.services.microsoft_entra_id import MicrosoftEntraID
from api.constants import ROUTE__ARES

ares_router = APIRouter(prefix=ROUTE__ARES)


async def get_microsoft_identity(request: Request) -> MicrosoftIdentity:
    return await MicrosoftEntraID.get_identity_from_request(request)


@ares_router.post(constants.ROUTE__LOGIN)
async def login(http_login: http.Login) -> MicrosoftIdentityToken:
    return await MicrosoftEntraID.get_access_token(http_login.application_name)


@ares_router.get(constants.ROUTE__GET_CURRENT_USER)
async def get_current_user(microsoft_identity: Annotated[MicrosoftIdentity, Depends(get_microsoft_identity)]) -> MicrosoftIdentity:
    return microsoft_identity
