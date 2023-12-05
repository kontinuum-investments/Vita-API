from typing import Dict

from sirius import common
from sirius.common import DataClass

from api.constants import BASE_URL, ROUTE__ATHENA
from api.exceptions import ClientException


class URL(DataClass):
    id: str
    url: str
    is_one_time: bool = False


class URLStore:
    store: Dict[str, URL] = {}

    @classmethod
    def put(cls, id_string: str, url: str, is_one_time: bool = False) -> None:
        cls.store[id_string] = URL(id=id_string, url=url, is_one_time=is_one_time)

    @classmethod
    def get(cls, id_string: str) -> URL:
        if id_string not in cls.store:
            raise ClientException(f"Unknown URL ID: {id_string}")

        url: URL = cls.store[id_string]
        if url.is_one_time:
            cls.store.pop(id_string)

        return url

    @classmethod
    def get_shortened_url(cls, id_string: str | None = None, url: str | None = None, is_one_time: bool = False) -> str:
        id_string = common.get_unique_id() if id_string is None else id_string
        if url is not None:
            URLStore.put(id_string, url, is_one_time)

        return f"{BASE_URL}{ROUTE__ATHENA}/{URLStore.get(id_string).id}"
