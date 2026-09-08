from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any, Protocol, cast

DEDUCTIONS = "deductions"
EMPLOYER_CONTRIBUTIONS = "employer_contributions"


class EarningRow(Protocol):
	salary_component: str
	amount: float


class SalaryComponentRow(Protocol):
	salary_component: str
	amount: float
	default_amount: float


class SalarySlipComponents(Protocol):
	_evaluated_components: Mapping[str, Iterable[SalaryComponentRow]]

	def get(self, fieldname: str) -> Iterable[SalaryComponentRow] | None: ...


class SalarySlipEarnings(Protocol):
	earnings: Iterable[EarningRow]


class MissingSalaryComponentError(LookupError):
	def __init__(self, component_table: str, component_name: str) -> None:
		self.component_table = component_table
		self.component_name = component_name
		label = component_table.replace("_", " ").removesuffix("s")
		super().__init__(f"Required {label} component '{component_name}' is missing from the Salary Slip")


def set_component_amount(
	salary_slip: SalarySlipComponents,
	component_table: str,
	component_name: str,
	amount: Decimal,
) -> None:
	"""Set an exact result on a configured Salary Slip component."""
	frappe_amount = as_frappe_currency(amount)
	components = salary_slip.get(component_table)
	if not components:
		components = getattr(salary_slip, "_evaluated_components", {}).get(component_table, ())

	for component in components:
		if component.salary_component == component_name:
			component.amount = frappe_amount
			component.default_amount = frappe_amount
			# Evaluated structure rows must not reevaluate their original formula later.
			if hasattr(component, "amount_based_on_formula"):
				evaluated_component = cast(Any, component)
				evaluated_component.amount_based_on_formula = 0
				evaluated_component.formula = None
			return

	raise MissingSalaryComponentError(component_table, component_name)


def as_frappe_currency(amount: Decimal) -> float:
	"""Convert to the numeric representation used by Frappe Currency fields."""
	return float(amount)
