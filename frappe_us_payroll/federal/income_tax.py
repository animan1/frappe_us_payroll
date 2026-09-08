from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from python_taxes.federal import income

FilingStatus = Literal["single", "married", "hoh"]
PayFrequency = Literal["monthly", "semimonthly", "biweekly", "weekly", "daily"]


@dataclass(frozen=True)
class FormW4:
	filing_status: FilingStatus
	multiple_jobs: bool = False
	dependents_amount: Decimal = Decimal("0.00")
	other_income: Decimal = Decimal("0.00")
	deductions: Decimal = Decimal("0.00")
	extra_withholding: Decimal = Decimal("0.00")


def calculate_federal_income_tax_withholding(
	*,
	taxable_wages: Decimal,
	pay_frequency: PayFrequency,
	form_w4: FormW4,
	tax_year: int,
) -> Decimal:
	"""Calculate withholding using Publication 15-T's automated percentage method."""
	return income.employer_withholding(
		taxable_wages=taxable_wages,
		pay_frequency=pay_frequency,
		filing_status=form_w4.filing_status,
		multiple_jobs=form_w4.multiple_jobs,
		tax_credits=form_w4.dependents_amount,
		other_income=form_w4.other_income,
		deductions=form_w4.deductions,
		extra_withholding=form_w4.extra_withholding,
		tax_year=tax_year,
		rounded=False,
	)
