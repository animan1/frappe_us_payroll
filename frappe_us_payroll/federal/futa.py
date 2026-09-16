from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


@dataclass(frozen=True)
class FutaRule:
	wage_base: Decimal
	effective_rate: Decimal


RULES = {
	2026: FutaRule(wage_base=Decimal("7000.00"), effective_rate=Decimal("0.006")),
}


def calculate_futa_liability(
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
	tax_year: int,
) -> Decimal:
	"""Calculate FUTA assuming eligibility for the maximum state-tax credit."""
	try:
		rule = RULES[tax_year]
	except KeyError as error:
		raise ValueError(f"FUTA rules are not available for {tax_year}") from error
	remaining_wage_base = max(rule.wage_base - prior_taxable_wages, Decimal("0.00"))
	current_taxable_wages = min(taxable_wages, remaining_wage_base)
	return (current_taxable_wages * rule.effective_rate).quantize(CENT, rounding=ROUND_HALF_UP)
