import datetime
from typing import List, Any, Dict, Tuple, cast

from _decimal import Decimal
from sirius import excel
from sirius.common import DataClass, Currency
from sirius.wise import ReserveAccount, Recipient, WiseAccount, WiseAccountType, CashAccount


class Summary(DataClass):
    salary: Decimal
    total_needs_expenses: Decimal
    total_wants_expenses: Decimal
    total_expenses: Decimal
    total_scheduled_transfers: Decimal
    savings: Decimal

    @staticmethod
    def get(excel_file_path: str) -> "Summary":
        excel_data: Dict[Any, Any] = excel.get_excel_data(excel_file_path, "Summary")[0]
        return Summary(salary=excel_data["Salary"],
                       total_needs_expenses=excel_data["Needs Expenses"],
                       total_wants_expenses=excel_data["Wants Expenses"],
                       total_expenses=excel_data["Total Expenses"],
                       total_scheduled_transfers=excel_data["Total Scheduled Transfers"],
                       savings=excel_data["Total Savings"])


class Settings(DataClass):
    salary: Decimal
    maximum_expenditure: Decimal
    monthly_needs_budget: Decimal
    monthly_wants_budget: Decimal
    fixed_expenses_account: Recipient

    @staticmethod
    def get(excel_file_path: str, wise_account: WiseAccount) -> "Settings":
        excel_data: Dict[Any, Any] = excel.get_excel_data(excel_file_path, "Settings")[0]
        return Settings(salary=cast(Decimal, excel_data["Salary"]),
                        maximum_expenditure=excel_data["Maximum Expenditure"],
                        monthly_needs_budget=excel_data["Monthly Needs Budget"],
                        monthly_wants_budget=excel_data["Monthly Wants Budget"],
                        fixed_expenses_account=wise_account.personal_profile.get_recipient(excel_data["Fixed Expenses Account Number"]),
                        savings_account=wise_account.personal_profile.get_recipient(excel_data["Savings Account Number"]))

    savings_account: Recipient


class FixedExpense(DataClass):
    description: str
    amount: Decimal
    currency: Currency


class Reserve(DataClass):
    reserve_account: ReserveAccount
    amount: Decimal


class ScheduledTransfer(DataClass):
    recipient: Recipient
    amount: Decimal


class MonthlyFinances(DataClass):
    excel_file_path: str
    fixed_expenses_need_list: List[FixedExpense]
    fixed_expenses_want_list: List[FixedExpense]
    reserve_need_list: List[Reserve]
    reserve_want_list: List[Reserve]
    scheduled_transfer_list: List[ScheduledTransfer]
    settings: Settings

    @staticmethod
    def _get_fixed_expenses(excel_file_path: str) -> Tuple[List[FixedExpense], List[FixedExpense]]:
        fixed_expenses_need_list: List[FixedExpense] = []
        fixed_expenses_want_list: List[FixedExpense] = []

        for sheet_name in ["Fixed Expenses (Needs)", "Fixed Expenses (Wants)"]:
            excel_data: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, sheet_name)
            fixed_expense_list: List[FixedExpense] = [FixedExpense(description=data["Description"], amount=data["Amount"], currency=Currency(data["Currency"])) for data in excel_data]
            fixed_expenses_need_list = fixed_expense_list if "need" in sheet_name.lower() else fixed_expenses_need_list
            fixed_expenses_want_list = fixed_expense_list if "want" in sheet_name.lower() else fixed_expenses_want_list

        return fixed_expenses_need_list, fixed_expenses_want_list

    @staticmethod
    def _get_reserve(excel_file_path: str, wise_account: WiseAccount) -> Tuple[List[Reserve], List[Reserve]]:
        reserve_need_list: List[Reserve] = []
        reserve_want_list: List[Reserve] = []

        for sheet_name in ["Reserve (Needs)", "Reserve (Wants)"]:
            excel_data: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, sheet_name)
            reserve_list: List[Reserve] = []

            for data in excel_data:
                reserve_account_name: str = data["Description"] + " (Needs)" if "need" in sheet_name.lower() else " (Wants)"
                reserve_list.append(Reserve(
                    reserve_account=wise_account.personal_profile.get_reserve_account(reserve_account_name, Currency(data["Currency"]), True),
                    amount=data["Amount"]
                ))

            reserve_need_list = reserve_list if "need" in sheet_name.lower() else reserve_need_list
            reserve_want_list = reserve_list if "want" in sheet_name.lower() else reserve_want_list

        return reserve_need_list, reserve_want_list

    @staticmethod
    def _get_scheduled_transfer_list(excel_file_path: str, wise_account: WiseAccount) -> List[ScheduledTransfer]:
        excel_data: List[Dict[Any, Any]] = excel.get_excel_data(excel_file_path, "Scheduled Transfers")
        return [ScheduledTransfer(recipient=wise_account.personal_profile.get_recipient(data["Account Number"]),
                                  amount=data["Amount"]) for data in excel_data]

    @staticmethod
    async def _transfer_scheduled_transfers(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        [await nzd_account.transfer(scheduled_transfer.recipient, scheduled_transfer.amount) for scheduled_transfer in monthly_finances.scheduled_transfer_list]

    @staticmethod
    async def _transfer_reserves(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        [await nzd_account.transfer(reserve.reserve_account, reserve.amount) for reserve in monthly_finances.reserve_need_list + monthly_finances.reserve_want_list]

    @staticmethod
    async def _transfer_fixed_expenses(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        total_fixed_expenses: Decimal = Decimal("0")

        for fixed_expense in monthly_finances.fixed_expenses_need_list + monthly_finances.fixed_expenses_want_list:
            total_fixed_expenses = total_fixed_expenses + fixed_expense.amount

        await nzd_account.transfer(monthly_finances.settings.fixed_expenses_account, total_fixed_expenses)

    @staticmethod
    async def _reserve_next_months_expenses(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        reserve_account: ReserveAccount = wise_account.personal_profile.get_reserve_account("Salary", Currency.NZD, True)
        next_months_expenses: Decimal = Decimal("0")

        for fixed_expense in monthly_finances.fixed_expenses_need_list + monthly_finances.fixed_expenses_want_list:
            next_months_expenses = next_months_expenses + fixed_expense.amount

        for reserve in monthly_finances.reserve_need_list + monthly_finances.reserve_want_list:
            next_months_expenses = next_months_expenses + reserve.amount

        await nzd_account.transfer(reserve_account, next_months_expenses)

    @staticmethod
    async def _transfer_savings(monthly_finances: "MonthlyFinances", wise_account: WiseAccount | None = None) -> None:
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        nzd_account: CashAccount = wise_account.personal_profile.get_cash_account(Currency.NZD)
        savings_account = monthly_finances.settings.savings_account
        total_fixed_expenses: Decimal = Decimal("0")
        total_reserve: Decimal = Decimal("0")

        for fixed_expense in monthly_finances.fixed_expenses_need_list + monthly_finances.fixed_expenses_want_list:
            total_fixed_expenses = total_fixed_expenses + fixed_expense.amount

        for reserve in monthly_finances.reserve_need_list + monthly_finances.reserve_want_list:
            total_reserve = total_reserve + reserve.amount

        savings: Decimal = nzd_account.balance - total_fixed_expenses - total_reserve
        await nzd_account.transfer(savings_account, savings)

    @staticmethod
    def get_monthly_finances(date: datetime.date, wise_account: WiseAccount | None = None) -> "MonthlyFinances":
        wise_account = WiseAccount.get(WiseAccountType.PRIMARY) if wise_account is None else wise_account
        excel_file_path: str = "C:/Users/kavin/Downloads/Oct, 2023.xlsx"
        fixed_expenses_need_list, fixed_expenses_want_list = MonthlyFinances._get_fixed_expenses(excel_file_path)
        reserve_need_list, reserve_want_list = MonthlyFinances._get_reserve(excel_file_path, wise_account)

        return MonthlyFinances(
            excel_file_path=excel_file_path,
            fixed_expenses_need_list=fixed_expenses_need_list,
            fixed_expenses_want_list=fixed_expenses_want_list,
            reserve_need_list=reserve_need_list,
            reserve_want_list=reserve_want_list,
            scheduled_transfer_list=MonthlyFinances._get_scheduled_transfer_list(excel_file_path, wise_account),
            settings=Settings.get(excel_file_path, wise_account)
        )

    @staticmethod
    async def organize_finances_when_salary_received() -> Summary:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        monthly_finances: MonthlyFinances = MonthlyFinances.get_monthly_finances(datetime.date.today(), wise_account)

        await MonthlyFinances._transfer_scheduled_transfers(monthly_finances, wise_account)
        await MonthlyFinances._reserve_next_months_expenses(monthly_finances, wise_account)
        await MonthlyFinances._transfer_savings(monthly_finances, wise_account)

        return Summary.get(monthly_finances.excel_file_path)

    @staticmethod
    async def organize_finances_for_next_month() -> Summary:
        wise_account: WiseAccount = WiseAccount.get(WiseAccountType.PRIMARY)
        monthly_finances: MonthlyFinances = MonthlyFinances.get_monthly_finances(datetime.date.today(), wise_account)

        await MonthlyFinances._transfer_reserves(monthly_finances, wise_account)
        await MonthlyFinances._transfer_fixed_expenses(monthly_finances, wise_account)

        return Summary.get(monthly_finances.excel_file_path)
