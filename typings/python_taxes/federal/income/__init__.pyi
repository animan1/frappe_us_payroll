from decimal import Decimal
from typing import Literal

def employer_withholding(
	taxable_wages: Decimal,
	pay_frequency: Literal[
		"semiannual", "quarterly", "monthly", "semimonthly", "biweekly", "weekly", "daily"
	] = ...,
	filing_status: Literal["single", "married", "separate", "hoh"] = ...,
	multiple_jobs: bool = ...,
	tax_credits: Decimal = ...,
	other_income: Decimal = ...,
	deductions: Decimal = ...,
	extra_withholding: Decimal = ...,
	tax_year: int = ...,
	rounded: bool = ...,
) -> Decimal: ...
