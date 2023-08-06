from typing import Dict, Any

from httpx import Response, AsyncClient, URL

from function_app import fast_app


async def get(url: str, **kwargs: Dict[str, Any]) -> Response:
    async with AsyncClient(app=fast_app, base_url="http://test") as ac:
        return await ac.get(URL(url), **kwargs)


async def put(url: str, **kwargs: Dict[str, Any]) -> Response:
    async with AsyncClient(app=fast_app, base_url="http://test") as ac:
        return await ac.put(URL(url), **kwargs)


async def post(url: str, **kwargs: Dict[str, Any]) -> Response:
    async with AsyncClient(app=fast_app, base_url="http://test") as ac:
        return await ac.post(URL(url), **kwargs)


async def delete(url: str, **kwargs: Dict[str, Any]) -> Response:
    async with AsyncClient(app=fast_app, base_url="http://test") as ac:
        return await ac.delete(URL(url), **kwargs)
