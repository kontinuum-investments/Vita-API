import datetime
from enum import Enum


class EnvironmentalVariable(Enum):
    MONTHLY_FINANCES_EXCEL_FILE_LINK: str = "MONTHLY_FINANCES_EXCEL_FILE_LINK"


def get_first_date_of_next_month(reference_month: datetime.date) -> datetime.date:
    next_month = reference_month.month + 1 if reference_month.month < 12 else 1
    next_year = reference_month.year if reference_month.month < 12 else reference_month.year + 1
    first_date_of_next_month = datetime.datetime(next_year, next_month, 1)
    return first_date_of_next_month
