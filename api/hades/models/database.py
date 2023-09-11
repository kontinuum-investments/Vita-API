from sirius.database import DatabaseDocument


class WiseAccountUpdate(DatabaseDocument):
    wise_delivery_id: str

    @classmethod
    async def is_duplicate(cls, wise_delivery_id: str) -> bool:
        return len(await cls.find_by_query(WiseAccountUpdate(wise_delivery_id=wise_delivery_id))) > 0
