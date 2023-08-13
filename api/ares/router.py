from fastapi import APIRouter
from sirius.iam.microsoft_entra_id import MicrosoftIdentityToken

from api.ares import constants
from api.ares.models import http
from api.ares.services.microsoft_entra_id import MicrosoftEntraID
from api.constants import ROUTE__ARES

ares_router = APIRouter(prefix=ROUTE__ARES)


@ares_router.post(constants.ROUTE__LOGIN)
async def login(http_login: http.Login) -> MicrosoftIdentityToken:
    return await MicrosoftEntraID.get_access_token(http_login.application_name)


@ares_router.post(constants.ROUTE__IS_ACCESS_TOKEN_VALID)
async def is_access_token_valid(access_token: str) -> bool:
    return await MicrosoftEntraID.is_access_token_valid(access_token)
