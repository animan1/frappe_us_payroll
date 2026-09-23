from dataclasses import dataclass
from decimal import Decimal

from frappe_us_payroll.federal.money import round_money


@dataclass(frozen=True)
class MedicareLiability:
	standard_employee: Decimal
	employer: Decimal
	additional_employee: Decimal

	@property
	def total_employee(self) -> Decimal:
		return self.standard_employee + self.additional_employee


def calculate_medicare_liability(
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
) -> MedicareLiability:
	"""Calculate current-period Medicare tax under IRS Publication 15."""
	employee_rate = Decimal("0.0145")
	additional_rate = Decimal("0.009")
	additional_threshold = Decimal("200000.00")
	over_threshold = min(
		taxable_wages,
		max(prior_taxable_wages + taxable_wages - additional_threshold, Decimal("0.00")),
	)
	standard = round_money(taxable_wages * employee_rate)
	additional = round_money(over_threshold * additional_rate)
	return MedicareLiability(
		standard_employee=standard,
		employer=standard,
		additional_employee=additional,
	)
