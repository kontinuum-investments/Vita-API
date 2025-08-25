import asyncio
from decimal import Decimal
from typing import List, Dict

import httpx
from fastapi import APIRouter
from sirius import common
from sirius.common import DataClass, Currency
from sirius.http_requests import AsyncHTTPSession, HTTPResponse

router = APIRouter()
_account_list: List["IBKRAccount"] = []
_account_list_lock = asyncio.Lock()


class Contract(DataClass):
    description: str
    currency: Currency
    position: Decimal
    average_cost: Decimal
    market_value: Decimal
    type: str

    @staticmethod
    async def get_all(account_id: str) -> List["Contract"]:
        contract_type_dict: Dict[str, str] = {"STK": "Stock", "OPT": "Option", "FUT": "Future", "FOP": "Future's Option", "BND": "Bond"}
        base_url: str = common.get_environmental_secret("IBKR_SERVICE_BASE_URL")
        url: str = f"{base_url}/portfolio/{account_id}/positions/"
        session: AsyncHTTPSession = AsyncHTTPSession(base_url)

        await session.client.aclose()
        session.client = httpx.AsyncClient(verify=False)
        response: HTTPResponse = await session.get(url)
        return [
            Contract(
                description=data["contractDesc"],
                currency=Currency(data["currency"]),
                position=Decimal(str(data["position"])),
                average_cost=Decimal(str(data["avgPrice"])),
                market_value=Decimal(str(data["mktPrice"])),
                type=contract_type_dict[data['assetClass']],
            )
            for data in response.data
        ]


class IBKRAccount(DataClass):
    id: str
    name: str
    contract_list: List[Contract] = []

    @staticmethod
    async def get_all_ibkr_accounts() -> List["IBKRAccount"]:
        global _account_list
        if len(_account_list) == 0:
            async with _account_list_lock:
                if len(_account_list) == 0:
                    base_url: str = common.get_environmental_secret("IBKR_SERVICE_BASE_URL")
                    url: str = f"{base_url}/portfolio/accounts/"
                    session: AsyncHTTPSession = AsyncHTTPSession(base_url)

                    await session.client.aclose()
                    session.client = httpx.AsyncClient(verify=False)
                    response: HTTPResponse = await session.get(url)

                    _account_list = [IBKRAccount(id=data["id"], name=data["accountAlias"] if data["accountAlias"] else data["id"]) for data in response.data]

        return _account_list


@router.get(
    "/account_summary",
    summary="Retrieves the Account Summary from all Interactive Brokers accounts.",
    description=(
            f"Note:\n"
            "    - Use the following examples to decode the pattern of the Contract Description\n"
            "        - An Option with a contract description of \"QQQ    SEP2025 610 C [QQQ   250919C00610000 100]\" can be decoded as\n"
            "            - Underlying Ticker: QQQ\n"
            "            - Strike Price: $610\n"
            "            - Type of Option: Call (because of the 'C' after in '610')\n"
            "            - Expiry: 2019-09-25 (because of the '250919' in the '250919C00610000')\n"
            "            - Multiplier: 100 (because of the '100' after the '250919C00610000')\n"
            "        - An Option with a contract description of \"QQQ    SEP2025 610 P [QQQ   250919C00610000 100]\" can be decoded as\n"
            "            - Underlying Ticker: QQQ\n"
            "            - Strike Price: $610\n"
            "            - Type of Option: Put (because of the 'P' after in '610')\n"
            "            - Expiry: 2019-09-25 (because of the '250919' in the '250919C00610000')\n"
            "            - Multiplier: 100 (because of the '100' after the '250919C00610000')\n"
            "        - A Future's Option with a contract description of \"NQ     MAR2026 23500 P\" can be decoded as\n"
            "            - Future's Ticker: NQ\n"
            "            - Future's Expiry: March 2026\n"
            "            - Strike Price: $23,500\n"
            "            - Type of Option: Put (because of the 'P' after in '23500')\n"
            "            - Future's Option's Expiry: March 2026\n"
            "        - A Future's Option with a contract description of \"NQ     MAR2026 26500 C\" can be decoded as\n"
            "            - Future's Ticker: NQ\n"
            "            - Future's Expiry: March 2026\n"
            "            - Strike Price: $26,500\n"
            "            - Type of Option: Call (because of the 'C' after in '26500')\n"
            "            - Future's Option's Expiry: March 2026\n"
            "        - A Future with a contract description of \"NQ       MAR2026\" can be decoded as\n"
            "            - Future's Ticker: NQ\n"
            "            - Future's Expiry: March 2026\n"
    ))
async def get_ibkr_account_summary() -> List[IBKRAccount]:
    account_list: List[IBKRAccount] = await IBKRAccount.get_all_ibkr_accounts()
    for account in account_list:
        account.contract_list = await Contract.get_all(account.id)

    return account_list

@router.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Hello World"}