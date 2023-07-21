from fastapi import APIRouter

hermes_router = APIRouter(prefix="/hermes")


@hermes_router.get("/test")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]
