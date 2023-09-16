import pytest

from api.hades.services.organize_monthly_finances import MonthlyFinances


class TestOrganizeMonthlyFinances:

    @pytest.mark.asyncio
    async def test_monthly_finances(self) -> None:
        await MonthlyFinances.organize_finances_for_next_month()
