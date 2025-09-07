import logging
from typing import List

from mcp.server.fastmcp import FastMCP
from sirius import common
from sirius.common import Currency
from sirius.http_requests import HTTPResponse, AsyncHTTPSession

API_BASE_URL: str = common.get_environmental_secret("VITA_API_BASE_URL")
mcp = FastMCP("Vita")
logging.basicConfig(level=logging.DEBUG)
session: AsyncHTTPSession = AsyncHTTPSession(API_BASE_URL, headers={"Authorization": f"Bearer {common.get_environmental_secret("API_KEY")}"})


@mcp.tool()
async def get_latest_wise_transactions(currency_str: str | None = None) -> str:
    """Fetches the most recent transactions from a Wise account.

    This function retrieves a list of transactions from the user's primary
    Wise personal cash account for a specified currency. It only considers
    transactions that have occurred within the last 24 hours.

    Args:
        currency_str: The ISO 4217 currency code for the account.
                  Defaults to "NZD" if not provided.

    Returns:
        A formatted string detailing recent transactions, with each entry
        containing the description and amount, separated by '---'.
        Returns an empty string if no transactions are found.
    """
    currency: Currency = Currency.NZD if currency_str is None else Currency(currency_str)
    response: HTTPResponse = await session.get(f"{API_BASE_URL}/wise/latest_transactions", query_params={"currency": currency.value})

    return '\n---\n'.join([
        f"Transaction Description: {data["description"]}\nTransaction Amount (in {data["currency"]}): ${data["amount"]}"
        for data in response.data
    ])


@mcp.tool()
async def get_wise_account_summary() -> str:
    """Provides a summary of all Wise cash and reserve accounts.

    This function iterates through all personal cash and reserve accounts
    linked to the user's primary Wise account and returns a summary
    of their names and current balances.

    Returns:
        A formatted string listing each account's name and balance,
        with individual account summaries separated by '---'.
    """
    response: HTTPResponse = await session.get(f"{API_BASE_URL}/wise/account_summary")
    return '\n---\n'.join([f"Account: {data["account_name"]}\nAccount Balance: {data["currency"]}{data["balance"]}" for data in response.data])


@mcp.tool()
async def send_discord_message(message: str) -> str:
    """Sends a specified message to a Discord channel.

        This function sends a Discord message to a Discord channel.

        Args:
            message: The string content of the message to be sent.

        Returns:
            A string indicating "Message sent successfully." if the message is sent.
        """
    await session.post(f"{API_BASE_URL}/discord/send_message", data={"message": "Hello World"})
    return 'Message sent'


@mcp.tool()
async def get_ibkr_account_summary() -> str:
    """Provides a detailed summary of all positions held in an Interactive Brokers (IBKR) account.

    IBKR is an acronym for Interactive Brokers, which is a stock brokerage. This function
    retrieves and formats information about the user's current holdings in their IBKR
    account, fetching account_data from an external service.

    Returns:
        A formatted string detailing each held position, with individual position
        summaries separated by '---'. Returns an empty string if no positions are found
        or if an error occurs during retrieval.
    """
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
    response: HTTPResponse = await session.get(f"{API_BASE_URL}/ibkr/account_summary")
    replies: List[str] = []
    for account_data in response.data:
        for contract_data in account_data["contract_list"]:
            replies.append((f"Account ID: {account_data["id"]}\n"
                            f"Sub-Account Name: {account_data["name"]}\n"
                            f"Contract Description: {contract_data['description']}\n"
                            f"Position: {contract_data['position']}\n"
                            f"Average Cost Price (the price you paid for it): {contract_data['currency']} {contract_data['average_cost']}\n"
                            f"Market Value: {contract_data['currency']} {contract_data['market_value']}\n"
                            f"Type of Contract: {contract_data['type']}\n"))

    reply: str = '\n---\n'.join(replies)
    return f"{reply}\n\n --- \n\n # Documentation\n{documentation}"


if __name__ == "__main__":
    mcp.run()
