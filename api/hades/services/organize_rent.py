import datetime
from typing import List

from _decimal import Decimal
from sirius import common
from sirius.common import DataClass, Currency
from sirius.communication.discord import TextChannel, get_timestamp_string
from sirius.wise import ReserveAccount, WiseAccount, WiseAccountType, CashAccount, Transaction

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.common import get_number_of_weekdays_in_month


class Tenant(DataClass):
    name: str
    name_substring_in_statement: str
    rent: Decimal
    reserve_account: ReserveAccount

    @property
    def is_sufficient_funds(self) -> bool:
        return self.amount_needed == Decimal("0")

    @property
    def amount_needed(self) -> Decimal:
        return max(self.rent - self.reserve_account.balance, Decimal("0"))

    @property
    def rent_paid_until(self) -> datetime.date:
        number_of_weeks: int = int(self.reserve_account.balance / self.rent) + 1
        return datetime.date.today() + datetime.timedelta(weeks=number_of_weeks)

    @staticmethod
    def get_all(wise_account: WiseAccount | None = None) -> List["Tenant"]:
        wise_account = WiseAccount.get(WiseAccountType.SECONDARY) if wise_account is None else wise_account
        tenant_list: List[Tenant] = [Tenant.model_construct(name="Kavindu Athaudha", name_substring_in_statement="JAYASEKARA", rent=Decimal("398.26")),
                                     Tenant.model_construct(name="Sayuru Jayasekara", name_substring_in_statement="Kavindu", rent=Decimal("397.50"))]
        for tenant in tenant_list:
            tenant.reserve_account = wise_account.personal_profile.get_reserve_account(tenant.name + " (Household Expenses)", Currency.NZD, True)

        return tenant_list

    @staticmethod
    async def process_incoming_transfer(transaction: Transaction) -> None:
        if not isinstance(transaction.third_party, str):
            return

        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.SECONDARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        tenant_list: List[Tenant] = Tenant.get_all(wise_account)

        for tenant in tenant_list:
            if not tenant.name_substring_in_statement.lower() in transaction.third_party.lower():
                continue

            amount_to_reserve: Decimal = transaction.amount
            if "kavindu" in tenant.name.lower():
                total_monthly_rent: Decimal = tenant.rent * Decimal(get_number_of_weekdays_in_month("Friday"))
                amount_to_reserve = max(amount_to_reserve, total_monthly_rent)

            await nzd_account.transfer(tenant.reserve_account, amount_to_reserve)


class OrganizeRent(DataClass):
    tenant_list: List[Tenant]

    @staticmethod
    async def do() -> "OrganizeRent":
        await Discord._initialize()
        text_channel: TextChannel = await Discord.server.get_text_channel(DiscordTextChannel.HOUSEHOLD_FINANCES.value, is_public_channel=False)
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.SECONDARY)
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        organize_rent: OrganizeRent = OrganizeRent(tenant_list=Tenant.get_all(wise_account))
        message: str = f"**Weekly Rental Notification:**\n"

        for tenant in organize_rent.tenant_list:
            message = message + f"*Tenant*: {tenant.name}\n"

            if tenant.is_sufficient_funds:
                await tenant.reserve_account.transfer(nzd_account, tenant.rent)
                message = message + f"*Rent paid until*: {get_timestamp_string(tenant.rent_paid_until)}\n" \
                                    f"*Account Balance*: {common.get_decimal_str(tenant.reserve_account.balance)}\n\n"
            else:
                message = message + f"__*Insufficient Funds*__\n" \
                                    f"*Account Balance*: {common.get_decimal_str(tenant.reserve_account.balance)}\n" \
                                    f"*Minimum Amount Needed*: {common.get_decimal_str(tenant.amount_needed)}\n\n"

        await text_channel.send_message(message)
        return organize_rent
