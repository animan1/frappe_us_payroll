from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True)
class MedicareLiability:
	employee: Decimal
	employer: Decimal
	additional_employee: Decimal


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
	standard = _money(taxable_wages * employee_rate)
	additional = _money(over_threshold * additional_rate)
	return MedicareLiability(
		employee=standard + additional,
		employer=standard,
		additional_employee=additional,
	)


def _money(value: Decimal) -> Decimal:
	return value.quantize(CENT, rounding=ROUND_HALF_UP)
