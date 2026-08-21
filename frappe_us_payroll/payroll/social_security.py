from collections.abc import Iterable, Set
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from frappe_us_payroll.federal.social_security import calculate_social_security_withholding
from frappe_us_payroll.payroll.components import (
	EarningRow,
	SalarySlipDeductions,
	SalarySlipEarnings,
	as_frappe_currency,
	set_deduction_amount,
)

SOCIAL_SECURITY_COMPONENT = "US Social Security"


class SocialSecuritySalarySlip(SalarySlipDeductions, SalarySlipEarnings, Protocol):
	posting_date: date | datetime | str
	us_social_security_taxable_wages: float


def taxable_wages(earnings: Iterable[EarningRow], taxable_components: Set[str]) -> Decimal:
	"""Total current-slip earnings whose components are subject to Social Security."""
	return sum(
		(Decimal(str(row.amount or 0)) for row in earnings if row.salary_component in taxable_components),
		start=Decimal("0"),
	)


def apply_social_security_withholding(
	salary_slip: SocialSecuritySalarySlip,
	*,
	taxable_components: Set[str],
	prior_taxable_wages: Decimal,
	opening_taxable_wages: Decimal,
) -> Decimal:
	"""Calculate and map employee Social Security withholding onto a Salary Slip."""
	current_taxable_wages = taxable_wages(salary_slip.earnings, taxable_components)
	withholding = calculate_social_security_withholding(
		taxable_wages=current_taxable_wages,
		prior_taxable_wages=prior_taxable_wages + opening_taxable_wages,
		tax_year=_posting_date(salary_slip.posting_date).year,
	)

	salary_slip.us_social_security_taxable_wages = as_frappe_currency(current_taxable_wages)
	set_deduction_amount(salary_slip, SOCIAL_SECURITY_COMPONENT, withholding)
	return withholding


def _posting_date(value: date | datetime | str) -> date:
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(value)
