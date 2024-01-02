from typing import Optional, List, Dict, Any

from sirius import excel, common
from sirius.common import DataClass, Currency
from sirius.wise import AccountCredit, AccountDebit, WiseAccount, WiseAccountType, ReserveAccount
from starlette.requests import Request

from api.athena.constants import DiscordTextChannel
from api.athena.services.discord import Discord
from api.hades.common import FinancesSettings


class AccountUpdate:

    @classmethod
    async def handle_account_update(cls, request: Request) -> None:
        await Discord.send_message(DiscordTextChannel.LOGS, await request.json())
        # wise_delivery_id: str = request.headers["X-Delivery-Id"]
        # request_data = await request.json()
        # if not common.is_development_environment() and await WiseAccountUpdate.is_duplicate(wise_delivery_id):
        #     await Logger.debug(f"Duplicate Wise account update received:\n{json.dumps(request_data)}")
        #
        # if request_data["data"]["resource"]["id"] == 0:
        #     await Logger.notify(f"Wise Webhook set up successfully")
        #
        # wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        # try:
        #     account_update: AccountDebit | AccountCredit | None = await WiseWebhook.get_balance_update_object(request_data, wise_account)
        # except Exception:
        #     await Logger.debug(f"Un-parsable Wise account update received:\n{json.dumps(request_data)}")
        #     return
        #
        # if isinstance(account_update, AccountCredit):
        #     asyncio.ensure_future(WiseCreditEvent.do(account_update))
        # elif isinstance(account_update, AccountDebit):
        #     asyncio.ensure_future(WiseDebitEvent.do(account_update))
        #
        # FinancesSettings.notify_if_only_cash_reserve_amount_present(wise_account)
        # await WiseAccountUpdate(wise_delivery_id=wise_delivery_id).save()


class WiseCreditEvent:
    @staticmethod
    async def do(account_credit: AccountCredit) -> None:
        expected_recipient: ExpectedRecipient | None = ExpectedRecipient.get(account_credit)
        await account_credit.account.transfer(expected_recipient.reserve_account, account_credit.transaction.amount)

        await Discord.send_message(DiscordTextChannel.WISE, f"**Account Credited**\n"
                                                            f"*From*: {account_credit.transaction.third_party if expected_recipient.name_in_statement == '' else expected_recipient.recipient_name}\n"
                                                            f"*Amount*: {account_credit.account.currency}{common.get_decimal_str(account_credit.transaction.amount)}\n"
                                                            f"*Balance of Reserve Account*: {account_credit.account.currency}{common.get_decimal_str(expected_recipient.reserve_account.balance)}")


class WiseDebitEvent:
    @staticmethod
    async def do(account_debit: AccountDebit) -> None:
        #   TODO
        pass


class ExpectedRecipient(DataClass):
    recipient_name: str
    name_in_statement: str
    reserve_account: ReserveAccount

    @staticmethod
    def get(account_credit: AccountCredit) -> Optional["ExpectedRecipient"]:
        if isinstance(account_credit.transaction.third_party, str):
            return ExpectedRecipient._get_by_name_in_statement(account_credit.transaction.third_party, account_credit.account.profile.wise_account)

        reserve_account: ReserveAccount = account_credit.account.profile.wise_account.personal_profile.get_reserve_account(f"Unknown [Reserve]", account_credit.account.currency, True)
        return ExpectedRecipient(
            recipient_name="Other",
            name_in_statement="",
            reserve_account=reserve_account
        )

    @staticmethod
    def get_all(wise_account: WiseAccount | None = None) -> List["ExpectedRecipient"]:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        excel_file_path: str = FinancesSettings.get_monthly_finances_excel_file_path()
        raw_recipient_list: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Expected Recipients")
        expected_recipient_list: List[ExpectedRecipient] = []

        for raw_recipient in raw_recipient_list:
            recipient_name: str = raw_recipient["Recipient Name"]
            name_in_statement: str = raw_recipient["Name in Statement"]
            currency: Currency = Currency(raw_recipient["Currency"])
            reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account(f"{recipient_name} [Reserve]", currency, True)

            expected_recipient_list.append(ExpectedRecipient(
                recipient_name=recipient_name,
                name_in_statement=name_in_statement,
                reserve_account=reserve_account
            ))

        return expected_recipient_list

    @staticmethod
    def _get_by_name_in_statement(name_in_statement: str, wise_account: WiseAccount) -> Optional["ExpectedRecipient"]:
        try:
            return next(filter(lambda e: e.name_in_statement.lower() == name_in_statement.lower(), ExpectedRecipient.get_all(wise_account)))
        except StopIteration:
            return None
