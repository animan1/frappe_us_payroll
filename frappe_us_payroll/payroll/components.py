from collections.abc import Iterable
from typing import Protocol


class DeductionRow(Protocol):
	salary_component: str
	amount: float
	default_amount: float


class SalarySlipDeductions(Protocol):
	def get(self, fieldname: str) -> Iterable[DeductionRow] | None: ...


class MissingSalaryComponentError(LookupError):
	def __init__(self, component_name: str) -> None:
		self.component_name = component_name
		super().__init__(f"Required deduction component '{component_name}' is missing from the Salary Slip")


def set_deduction_amount(
	salary_slip: SalarySlipDeductions,
	component_name: str,
	amount: float,
) -> None:
	"""Set a required deduction row, failing if the Salary Structure omitted it."""
	for deduction in salary_slip.get("deductions") or ():
		if deduction.salary_component == component_name:
			deduction.amount = amount
			deduction.default_amount = amount
			return

	raise MissingSalaryComponentError(component_name)
