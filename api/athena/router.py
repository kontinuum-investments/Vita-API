from typing import List, Dict, Any

from fastapi import APIRouter

from api.constants import ROUTE__ATHENA

athena_router = APIRouter(prefix=ROUTE__ATHENA)


@athena_router.get("/test")
async def read_users() -> List[Dict[str, Any]]:
    return [{"username": "Rick"}, {"username": "Morty"}]
