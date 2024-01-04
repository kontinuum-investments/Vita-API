import datetime

import pytest
from sirius.http_requests import ServerSideException

from api.hades.services.transaction_organisation import WiseDebitEvent


# @pytest.mark.skip("Requires verification in Wise Sandbox to transfer savings")
@pytest.mark.xfail(raises=ServerSideException)
@pytest.mark.asyncio
async def test_transaction_organisation() -> None:
    await WiseDebitEvent.organise_transactions(datetime.datetime.now() - datetime.timedelta(days=1))
