from decimal import ROUND_HALF_UP, Decimal

from python_taxes.federal import social_security


CENT = Decimal("0.01")


def calculate_social_security_withholding(
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
	tax_year: int,
) -> Decimal:
	"""Calculate employee Social Security withholding for a pay period."""
	assert isinstance(taxable_wages, Decimal)
	assert isinstance(prior_taxable_wages, Decimal)
	taxable_wages = taxable_wages.quantize(CENT, rounding=ROUND_HALF_UP)
	taxable_wages_ytd = prior_taxable_wages.quantize(CENT, rounding=ROUND_HALF_UP)
	return social_security.withholding(
		taxable_wages=taxable_wages,
		taxable_wages_ytd=taxable_wages_ytd,
		self_employed=False,
		tax_year=tax_year,
		rounded=False,
	)
