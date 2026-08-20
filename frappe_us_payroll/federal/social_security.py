from dataclasses import dataclass
from decimal import Decimal

from python_taxes.federal import social_security


@dataclass(frozen=True)
class SocialSecurityCalculation:
	employee_withholding: Decimal
	employer_liability: Decimal


def calculate_social_security(
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
	tax_year: int,
) -> SocialSecurityCalculation:
	"""Calculate both shares of Social Security tax for an employee pay period."""
	employee_withholding = social_security.withholding(
		taxable_wages=taxable_wages,
		taxable_wages_ytd=prior_taxable_wages,
		self_employed=False,
		tax_year=tax_year,
		rounded=False,
	)

	return SocialSecurityCalculation(
		employee_withholding=employee_withholding,
		employer_liability=employee_withholding,
	)
