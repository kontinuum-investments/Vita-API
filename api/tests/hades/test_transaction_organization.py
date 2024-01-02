from decimal import Decimal
from decimal import Decimal
from typing import Dict, Any

import pytest
from httpx import Response
from sirius import common
from sirius.common import Currency
from sirius.http_requests import ServerSideException
from sirius.wise import WiseAccount, WiseAccountType, CashAccount

from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.common import FinancesSettings
from api.tests import post


class TestAccountUpdate:
    @pytest.mark.skip("Requires an actual transaction")
    @pytest.mark.xfail(raises=ServerSideException)
    @pytest.mark.asyncio
    async def test_incoming_bank_transfer(self) -> None:
        cash_reserve_amount: Decimal = FinancesSettings.get_cash_reserve_amount()
        transfer_amount: Decimal = Decimal("108.32")
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        headers: Dict[str, Any] = {"X-Delivery-Id": common.get_unique_id()}
        data: Dict[str, Any] = {
            "data": {
                "resource": {
                    "id": 7155476,
                    "profile_id": 16336678,
                    "type": "balance-account"
                },
                "amount": common.get_decimal_str(transfer_amount),
                "currency": "NZD",
                "post_transaction_balance_amount": 1.0,
                "occurred_at": "2024-01-02T02:57:27Z",
                "transaction_type": "credit"
            },
            "subscription_id": "b15022a1-7d28-42d4-a0b6-653a218f6e9e",
            "event_type": "balances#credit",
            "schema_version": "2.0.0",
            "sent_at": "2024-01-02T02:57:28Z"
        }
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        await nzd_account._set_balance(cash_reserve_amount)

        response: Response = await post(f"{ROUTE__HADES}{constants.ROUTE__WEBHOOK_WISE__ACCOUNT_UPDATE}", data=data, headers=headers)
        assert response.status_code == 200
