from collections.abc import Iterable
from decimal import Decimal
from typing import Protocol


class EarningRow(Protocol):
	salary_component: str
	amount: float


class DeductionRow(Protocol):
	salary_component: str
	amount: float
	default_amount: float


class SalarySlipDeductions(Protocol):
	def get(self, fieldname: str) -> Iterable[DeductionRow] | None: ...


class SalarySlipEarnings(Protocol):
	earnings: Iterable[EarningRow]


class MissingSalaryComponentError(LookupError):
	def __init__(self, component_name: str) -> None:
		self.component_name = component_name
		super().__init__(f"Required deduction component '{component_name}' is missing from the Salary Slip")


def set_deduction_amount(
	salary_slip: SalarySlipDeductions,
	component_name: str,
	amount: Decimal,
) -> None:
	"""Set an exact deduction result at Frappe's float-valued document boundary."""
	frappe_amount = as_frappe_currency(amount)
	for deduction in salary_slip.get("deductions") or ():
		if deduction.salary_component == component_name:
			deduction.amount = frappe_amount
			deduction.default_amount = frappe_amount
			return

	raise MissingSalaryComponentError(component_name)


def as_frappe_currency(amount: Decimal) -> float:
	"""Convert to the numeric representation used by Frappe Currency fields."""
	return float(amount)
