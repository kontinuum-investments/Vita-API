import asyncio
import datetime
import json
from typing import Dict, Any, List

import fastapi
from sirius.common import DataClass
from sirius.database import DatabaseDocument
from starlette.concurrency import iterate_in_threadpool
from starlette.responses import StreamingResponse


class Response(DataClass):
    body: Dict[str, Any]
    headers: Dict[str, Any]


class Request(DataClass):
    query_params: Dict[str, Any] | None
    body: Dict[str, Any] | None
    headers: Dict[str, Any]
    ip_address: str
    port_number: int


class HTTPExchange(DatabaseDocument):
    request: Request
    response: Response
    timestamp: datetime.datetime

    #   TODO: Create a clean-up job
    @staticmethod
    async def log_request(fast_api_request: fastapi.Request, fast_api_response: StreamingResponse) -> None:
        response_body: List[bytes] = [chunk async for chunk in fast_api_response.body_iterator]  # type:ignore[misc]
        fast_api_response.body_iterator = iterate_in_threadpool(iter(response_body))
        response_body_string: str = (b''.join(response_body)).decode()
        fast_api_response.body_iterator = iterate_in_threadpool(iter(response_body))
        response: Response = Response(body=json.loads(response_body_string) if response_body_string != "" else None,
                                      headers=dict(fast_api_response.headers))

        request_query_params: Dict[str, Any] = dict(fast_api_request.query_params)
        request_body_string: str = (await fast_api_request.body()).decode("UTF-8")
        request: Request = Request(query_params=request_query_params if len(request_query_params) > 0 else None,
                                   body=json.loads(request_body_string) if request_body_string != "" else None,
                                   headers=dict(fast_api_request.headers),
                                   ip_address=fast_api_request.get("client")[0],
                                   port_number=fast_api_request.get("client")[1])

        asyncio.ensure_future(HTTPExchange(request=request, response=response, timestamp=datetime.datetime.utcnow()).save())
