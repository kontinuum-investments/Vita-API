from typing import List, Dict, Any

from fastapi import APIRouter

from api.constants import ROUTE__ARES

ares_router = APIRouter(prefix=ROUTE__ARES)


@ares_router.get("/test")
async def read_users() -> List[Dict[str, Any]]:
    return [{"username": "Rick"}, {"username": "Morty"}]
