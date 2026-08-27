from collections.abc import Iterable
from decimal import Decimal
from typing import Protocol


DEDUCTIONS = "deductions"
EMPLOYER_CONTRIBUTIONS = "employer_contributions"


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


def set_component_amount(
	salary_slip: SalarySlipDeductions,
	component_type: str,
	component_name: str,
	amount: Decimal,
) -> None:
	"""Set an exact deduction result at Frappe's float-valued document boundary."""
	frappe_amount = as_frappe_currency(amount)
	components = salary_slip.get(component_type)
	if components is None:
		components = salary_slip._evaluated_components[component_type]
	for comp in components:
		if comp.salary_component == component_name:
			comp.amount = frappe_amount
			comp.default_amount = frappe_amount
			return
	raise ValueError(salary_slip.as_dict())
	raise MissingSalaryComponentError(component_name)


def as_frappe_currency(amount: Decimal) -> float:
	"""Convert to the numeric representation used by Frappe Currency fields."""
	return float(amount)
