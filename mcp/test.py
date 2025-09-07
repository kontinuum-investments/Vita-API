from dotenv import load_dotenv

load_dotenv()
import pytest
from fastmcp import Client

client = Client("main.py")


@pytest.mark.asyncio
async def test_get_latest_transactions() -> None:
    async with client:
        result = await client.call_tool("get_latest_wise_transactions", {"currency": "NZD"})
        result_string: str = result.content[0].text  # type: ignore[union-attr]
        assert result_string is not None and result_string != ""
        print(result.content[0].text)  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_get_account_summary() -> None:
    async with client:
        result = await client.call_tool("get_wise_account_summary", None)
        result_string: str = result.content[0].text  # type: ignore[union-attr]
        assert result_string is not None and result_string != ""
        print(result.content[0].text)  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_send_discord_message() -> None:
    async with client:
        result = await client.call_tool("send_discord_message", {"message": "Hello World"})
        result_string: str = result.content[0].text  # type: ignore[union-attr]
        assert result_string is not None and result_string != ""
        print(result.content[0].text)  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_get_ibkr_account_summary() -> None:
    async with client:
        result = await client.call_tool("get_ibkr_account_summary", None)
        result_string: str = result.content[0].text  # type: ignore[union-attr]
        assert result_string is not None and result_string != ""
        print(result.content[0].text)  # type: ignore[union-attr]
