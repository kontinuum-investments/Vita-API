from typing import Dict, Any

from httpx import Response, AsyncClient, URL

from main import app

authentication_header: Dict[str, Any] = {"Authorization": "Bearer 1234"}


async def get(url: str, **kwargs: Dict[str, Any]) -> Response:
    if kwargs.get("headers") is None:
        kwargs["headers"] = authentication_header

    async with AsyncClient(app=app, base_url="http://test") as ac:
        return await ac.get(URL(url), **kwargs)  # type: ignore[arg-type]


async def put(url: str, **kwargs: Dict[str, Any]) -> Response:
    if kwargs.get("headers") is None:
        kwargs["headers"] = authentication_header

    async with AsyncClient(app=app, base_url="http://test") as ac:
        return await ac.put(URL(url), **kwargs)  # type: ignore[arg-type]


async def post(url: str, **kwargs: Dict[str, Any]) -> Response:
    if kwargs.get("headers") is None:
        kwargs["headers"] = authentication_header

    async with AsyncClient(app=app, base_url="http://test") as ac:
        return await ac.post(URL(url), **kwargs)  # type: ignore[arg-type]


async def delete(url: str, **kwargs: Dict[str, Any]) -> Response:
    if kwargs.get("headers") is None:
        kwargs["headers"] = authentication_header

    async with AsyncClient(app=app, base_url="http://test") as ac:
        return await ac.delete(URL(url), **kwargs)  # type: ignore[arg-type]
