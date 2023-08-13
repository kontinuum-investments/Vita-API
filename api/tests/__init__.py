from typing import Dict, Any

from httpx import Response, AsyncClient, URL

from main import app


async def get(url: str, **kwargs: Dict[str, Any]) -> Response:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        return await ac.get(URL(url), **kwargs)  # type: ignore[arg-type]


async def put(url: str, **kwargs: Dict[str, Any]) -> Response:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        return await ac.put(URL(url), **kwargs)  # type: ignore[arg-type]


async def post(url: str, **kwargs: Dict[str, Any]) -> Response:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        return await ac.post(URL(url), **kwargs)  # type: ignore[arg-type]


async def delete(url: str, **kwargs: Dict[str, Any]) -> Response:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        return await ac.delete(URL(url), **kwargs)  # type: ignore[arg-type]
