import datetime
import json
from json import JSONDecodeError
from typing import Dict, Any, List

from sirius import common
from sirius.common import DataClass
from sirius.database import DatabaseDocument
from starlette import requests
from starlette.concurrency import iterate_in_threadpool
from starlette.responses import StreamingResponse


class Response(DataClass):
    body: Dict[str, Any] | str | None
    headers: Dict[str, Any]


class Request(DataClass):
    query_params: Dict[str, Any] | None
    body: Dict[str, Any] | str | None
    headers: Dict[str, Any]
    ip_address: str
    port_number: int


class HTTPExchange(DatabaseDocument):
    request: Request
    response: Response
    timestamp: datetime.datetime

    #   TODO: Create a clean-up job
    @staticmethod
    async def log_request(fast_api_request: requests.Request, fast_api_response: StreamingResponse) -> None:
        if common.is_development_environment():
            return

        await HTTPExchange(request=await HTTPExchange._get_request(fast_api_request),
                           response=await HTTPExchange._get_response(fast_api_response),
                           timestamp=datetime.datetime.utcnow()).save()

    @staticmethod
    async def _get_response(fast_api_response: StreamingResponse) -> Response:
        response_body_bytes_list: List[bytes] = [chunk async for chunk in fast_api_response.body_iterator]  # type:ignore[misc]
        fast_api_response.body_iterator = iterate_in_threadpool(iter(response_body_bytes_list))
        response_body_string: str = (b''.join(response_body_bytes_list)).decode()
        fast_api_response.body_iterator = iterate_in_threadpool(iter(response_body_bytes_list))
        try:
            response_body: Dict[str, Any] | str | None = json.loads(response_body_string)
        except JSONDecodeError:
            response_body = response_body_string if response_body_string != "" and response_body_string != "null" else None

        return Response(body=response_body, headers=dict(fast_api_response.headers))

    @staticmethod
    async def _get_request(fast_api_request: requests.Request) -> Request:
        request_query_params: Dict[str, Any] = dict(fast_api_request.query_params)
        request_body_string: str = (await fast_api_request.body()).decode("UTF-8")

        async def get_body() -> bytes:
            return request_body_string.encode()

        fast_api_request.body = get_body  # type:ignore[method-assign]

        try:
            request_body: Dict[str, Any] | str | None = json.loads(request_body_string)
        except JSONDecodeError:
            request_body = request_body_string if request_body_string != "" and request_body_string != "null" else None

        return Request(query_params=request_query_params if len(request_query_params) > 0 else None,
                       body=request_body,
                       headers=dict(fast_api_request.headers),
                       ip_address=fast_api_request.get("client")[0],
                       port_number=fast_api_request.get("client")[1])
