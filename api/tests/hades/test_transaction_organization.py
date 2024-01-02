from decimal import Decimal
from typing import Dict, Any

import pytest
from httpx import Response
from sirius.common import Currency
from sirius.http_requests import ServerSideException
from sirius.wise import WiseAccount, WiseAccountType, ReserveAccount, CashAccount

from api.constants import ROUTE__HADES
from api.hades import constants
from api.hades.common import FinancesSettings
from api.tests import post


class TestAccountUpdate:
    @pytest.mark.skip("Requires verification in Wise Sandbox to transfer savings")
    @pytest.mark.xfail(raises=ServerSideException)
    @pytest.mark.asyncio
    async def test_incoming_bank_transfer(self) -> None:
        cash_reserve_amount: Decimal = FinancesSettings.get_cash_reserve_amount()
        transfer_amount: Decimal = Decimal("108.32")
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        headers: Dict[str, Any] = {}
        data: Dict[str, Any] = {
            "data": {
                "resource": {
                    "type": "balance-account",
                    "id": 111,
                    "profile_id": 222
                },
                "transaction_type": "credit",
                "amount": 1.23,
                "currency": "EUR",
                "post_transaction_balance_amount": 2.34,
                "occurred_at": "2020-01-01T12:34:56Z"
            },
            "subscription_id": "01234567-89ab-cdef-0123-456789abcdef",
            "event_type": "balances#credit",
            "schema_version": "2.0.0",
            "sent_at": "2020-01-01T12:34:56Z"
        }
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        await nzd_account._set_balance(cash_reserve_amount)

        response: Response = await post(f"{ROUTE__HADES}{constants.ROUTE__WEBHOOK_WISE__ACCOUNT_UPDATE}", data=data)
        reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account("Sayuru Jayasekara [Reserve]", Currency.NZD)

        assert response.status_code == 200
        assert reserve_account.balance == transfer_amount
        assert nzd_account.balance == cash_reserve_amount
