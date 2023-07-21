from fastapi import APIRouter

hades_router = APIRouter(prefix="/hades")


@hades_router.get("/test")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]
