from fastapi import APIRouter
from sirius.iam.microsoft_entra_id import MicrosoftIdentityToken

from api.ares import constants
from api.constants import ROUTE__ARES

ares_router = APIRouter(prefix=ROUTE__ARES)


@ares_router.post(constants.ROUTE__LOGIN)
async def login() -> MicrosoftIdentityToken:
    return await MicrosoftIdentityToken.get_token(["User.Read"])


@ares_router.post(constants.ROUTE__VALIDATE_ACCESS_TOKEN)
async def validate_token(access_token: str) -> bool:
    return await MicrosoftIdentityToken.validate_token(access_token)
