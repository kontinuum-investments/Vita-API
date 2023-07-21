from fastapi import APIRouter

ares_router = APIRouter(prefix="/ares")


@ares_router.get("/test")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]
