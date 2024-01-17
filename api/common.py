import calendar
import datetime
from enum import Enum

from sirius.database import ConfigurationEnum

from api.exceptions import VitaException


class EnvironmentalSecret(ConfigurationEnum):
    MONTHLY_FINANCES_EXCEL_FILE_LINK: str = "MONTHLY-FINANCES-EXCEL-FILE-LINK"


def get_first_date_of_next_month(reference_month: datetime.date) -> datetime.date:
    next_month: int = reference_month.month + 1 if reference_month.month < 12 else 1
    next_year: int = reference_month.year if reference_month.month < 12 else reference_month.year + 1
    return datetime.datetime(next_year, next_month, 1).date()


def is_last_day_of_month(date: datetime.date | None = None) -> bool:
    date = datetime.date.today() if date is None else date
    return (date + datetime.timedelta(days=1)).day == 1


def get_number_of_weekdays_in_month(day_of_the_week_str: str, month_date: datetime.date | None = None) -> int:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day_of_the_week_str not in days:
        raise VitaException(f"Invalid day of the week: {day_of_the_week_str}")

    month_date = datetime.date.today() if month_date is None else month_date
    day_of_the_week_index: int = days.index(day_of_the_week_str)
    month = month_date.month
    year = month_date.year
    num_days: int = calendar.monthrange(year, month)[1]
    first_day_of_month_day_index: int = datetime.datetime(year, month, 1).weekday()

    return sum(1 for day in range(1, num_days + 1) if (first_day_of_month_day_index + day - 1) % 7 == day_of_the_week_index)
