from fastapi import APIRouter

chronos_router = APIRouter(prefix="/chronos")


@chronos_router.get("/test")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]
