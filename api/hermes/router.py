from typing import Any, Dict, List

from fastapi import APIRouter

from api.constants import ROUTE__HERMES

hermes_router = APIRouter(prefix=ROUTE__HERMES)


@hermes_router.get("/test")
async def read_users() -> List[Dict[str, Any]]:
    return [{"username": "Rick"}, {"username": "Morty"}]
