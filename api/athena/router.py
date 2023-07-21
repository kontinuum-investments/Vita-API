from fastapi import APIRouter

athena_router = APIRouter(prefix="/athena")


@athena_router.get("/test")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]
