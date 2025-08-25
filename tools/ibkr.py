import os
from typing import List, Dict

import httpx
from sirius.common import DataClass
from sirius.http_requests import AsyncHTTPSession, HTTPResponse

import asyncio

_account_list: List["IBKRAccount"] = []
_account_list_lock = asyncio.Lock()


class IBKRAccount(DataClass):
    id: str
    name: str


async def get_all_ibkr_accounts(session: AsyncHTTPSession) -> List[IBKRAccount]:
    global _account_list
    if len(_account_list) == 0:
        async with _account_list_lock:
            if len(_account_list) == 0 is None:
                base_url: str = os.getenv("IBKR_SERVICE_BASE_URL")
                url: str = f"{base_url}/portfolio/accounts/"
                response: HTTPResponse = await session.get(url)

                _account_list = [IBKRAccount(id=data["id"], name=data["accountAlias"]) for data in response.data]

    return _account_list


async def get_ibkr_account_summary() -> str:
    documentation: str = (
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
    )
    reply: str = ""
    contract_type_dict: Dict[str, str] = {"STK": "Stock", "OPT": "Option", "FUT": "Future", "FOP": "Future's Option", "BND": "Bond"}
    base_url: str = os.getenv("IBKR_SERVICE_BASE_URL")
    session: AsyncHTTPSession = AsyncHTTPSession(base_url)

    await session.client.aclose()
    session.client = httpx.AsyncClient(verify=False)

    account_list: List[IBKRAccount] = await get_all_ibkr_accounts(session)
    for account in account_list:
        url: str = f"{base_url}/portfolio/{account.id}/positions/"
        response: HTTPResponse = await session.get(url)

        for data in response.data:
            reply = (f"{reply}"
                     f"\n---\n"
                     f"Sub-Account Name: {account.name}\n"
                     f"Contract Description: {data['contractDesc']}\n"
                     f"Position: {data['position']}\n"
                     f"Average Cost Price (the price you paid for it): {data['currency']} {data['avgPrice']}\n"
                     f"Market Value: {data['currency']} {data['mktPrice']}\n"
                     f"Type of Contract: {contract_type_dict[data['assetClass']]}\n"
                     f"Strike Price (if the contract is an Option): {data['currency']} {data['strike']}"
                     f"\n---\n")

    return (f"{reply}"
            f"\n---\n"
            f"# Documentation\n"
            f"{documentation}")
