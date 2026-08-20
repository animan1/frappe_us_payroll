from decimal import Decimal

from python_taxes.federal import social_security


def calculate_social_security_withholding(
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
	tax_year: int,
) -> Decimal:
	"""Calculate employee Social Security withholding for a pay period."""
	return social_security.withholding(
		taxable_wages=taxable_wages,
		taxable_wages_ytd=prior_taxable_wages,
		self_employed=False,
		tax_year=tax_year,
		rounded=False,
	)
