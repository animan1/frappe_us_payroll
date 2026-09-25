from decimal import Decimal

from frappe_us_payroll.federal.income_tax import (
	FormW4,
	PayFrequency,
	calculate_federal_income_tax_withholding,
)
from frappe_us_payroll.payroll.component_names import FEDERAL_INCOME_TAX
from frappe_us_payroll.payroll.components import DEDUCTIONS, set_component_amount
from frappe_us_payroll.payroll.dates import as_date
from frappe_us_payroll.payroll.protocols import FederalIncomeTaxSalarySlip


def apply_federal_income_tax_withholding(
	salary_slip: FederalIncomeTaxSalarySlip,
	*,
	taxable_wages: Decimal,
	form_w4: FormW4,
) -> Decimal:
	withholding = calculate_federal_income_tax_withholding(
		taxable_wages=taxable_wages,
		pay_frequency=_pay_frequency(salary_slip.payroll_frequency),
		form_w4=form_w4,
		tax_year=as_date(salary_slip.posting_date).year,
	)
	set_component_amount(salary_slip, DEDUCTIONS, FEDERAL_INCOME_TAX, withholding)
	return withholding


def _pay_frequency(value: str) -> PayFrequency:
	frequencies: dict[str, PayFrequency] = {
		"Monthly": "monthly",
		"Bimonthly": "semimonthly",
		"Fortnightly": "biweekly",
		"Weekly": "weekly",
		"Daily": "daily",
	}
	try:
		return frequencies[value]
	except KeyError as error:
		raise ValueError(f"Unsupported payroll frequency: {value or '(blank)'}") from error
