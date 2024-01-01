# import datetime
#
# import pytest
# from _decimal import Decimal
#
# from sirius.http_requests import ServerSideException
# from sirius.wise import WiseAccount, WiseAccountType
#
# from api.hades.services.organize_rent import Tenant, OrganizeRent
#
#
# class TestOrganizeRent:
#
#     @pytest.mark.xfail(raises=ServerSideException)
#     @pytest.mark.asyncio
#     async def test_insufficient_funds(self) -> None:
#         wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
#         tenant: Tenant = next(filter(lambda t: "kavindu" in t.name.lower(), Tenant.get_all(wise_account)))
#         await tenant.reserve_account._set_balance(tenant.rent - Decimal("1"))
#         organize_rent: OrganizeRent = await OrganizeRent.do()
#         actual_tenant: Tenant = next(filter(lambda t: "kavindu" in t.name.lower(), organize_rent.tenant_list))
#
#         assert not actual_tenant.is_sufficient_funds
#         assert actual_tenant.amount_needed == Decimal("1")
#         assert actual_tenant.rent_paid_until == (datetime.date.today() + datetime.timedelta(weeks=1))
#
#     @pytest.mark.xfail(raises=ServerSideException)
#     @pytest.mark.asyncio
#     async def test_sufficient_funds(self) -> None:
#         wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
#         tenant: Tenant = next(filter(lambda t: "kavindu" in t.name.lower(), Tenant.get_all(wise_account)))
#         await tenant.reserve_account._set_balance(tenant.rent * Decimal(4))
#         organize_rent: OrganizeRent = await OrganizeRent.do()
#         actual_tenant: Tenant = next(filter(lambda t: "kavindu" in t.name.lower(), organize_rent.tenant_list))
#
#         assert actual_tenant.is_sufficient_funds
#         assert actual_tenant.amount_needed == Decimal("0")
#         assert actual_tenant.rent_paid_until == (datetime.date.today() + datetime.timedelta(weeks=4))
