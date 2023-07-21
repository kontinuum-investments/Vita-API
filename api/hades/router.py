from fastapi import APIRouter
from sirius import common

hades_router = APIRouter(prefix="/hades")


@hades_router.get("/test")
async def read_users():
    return [{"currency": f"{common.Currency.AED.value}"}]

