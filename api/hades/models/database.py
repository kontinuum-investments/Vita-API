from typing import Union

from sirius.database import DatabaseDocument
from sirius.wise import AccountDebit, AccountCredit, WiseAccountType


class WiseAccountUpdate(DatabaseDocument):
    wise_id: int
    wise_account_type: str

    @staticmethod
    def _get_from_account_update(wise_account_type: WiseAccountType, account_update: AccountDebit | AccountCredit) -> "WiseAccountUpdate":
        return WiseAccountUpdate(wise_id=account_update.wise_id, wise_account_type="Primary" if wise_account_type.PRIMARY else "Secondary")

    @classmethod
    async def save_to_database(cls, wise_account_type: WiseAccountType, account_update: AccountDebit | AccountCredit | None) -> Union["WiseAccountUpdate", None]:
        if account_update is None or (isinstance(account_update, AccountDebit) and not account_update.is_successful):
            return None

        wise_account_update: WiseAccountUpdate = cls._get_from_account_update(wise_account_type, account_update)
        await wise_account_update.save()
        return wise_account_update

    @classmethod
    async def is_duplicate(cls, wise_account_type: WiseAccountType, account_update: AccountDebit | AccountCredit | None) -> bool:
        if account_update is None or (isinstance(account_update, AccountDebit) and not account_update.is_successful):
            return False

        wise_account_update: WiseAccountUpdate = cls._get_from_account_update(wise_account_type, account_update)
        return len(await cls.find_by_query(wise_account_update)) > 0
