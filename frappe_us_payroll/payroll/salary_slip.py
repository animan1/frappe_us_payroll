from datetime import date
from decimal import Decimal
from typing import Protocol, cast

import frappe

from frappe_us_payroll.payroll.components import MissingSalaryComponentError
from frappe_us_payroll.payroll.social_security import (
	SocialSecuritySalarySlip,
	apply_social_security_withholding,
)

OPENING_WAGES_FIELD = "us_social_security_taxable_wages_till_date"
SLIP_WAGES_FIELD = "us_social_security_taxable_wages"


class SalaryStructureAssignment(Protocol):
	def get(self, fieldname: str) -> str | int | float | None: ...


class FrappeSalarySlip(SocialSecuritySalarySlip, Protocol):
	name: str
	employee: str
	_salary_structure_assignment: SalaryStructureAssignment


def apply_us_payroll_deductions(salary_slip: FrappeSalarySlip) -> None:
	"""Apply supported US deductions through HRMS's regional extension point."""
	try:
		apply_social_security_withholding(
			salary_slip,
			taxable_components=_taxable_social_security_components(),
			prior_taxable_wages=_prior_social_security_wages(salary_slip),
			opening_taxable_wages=_decimal(salary_slip._salary_structure_assignment.get(OPENING_WAGES_FIELD)),
		)
	except MissingSalaryComponentError as error:
		frappe.throw(str(error), exc=frappe.ValidationError, title="US Payroll Configuration Required")


def _taxable_social_security_components() -> set[str]:
	values = frappe.get_all(
		"Salary Component",
		filters={"type": "Earning", "disabled": 0, "us_social_security_taxable": 1},
		pluck="name",
	)
	return set(cast(list[str], values))


def _prior_social_security_wages(salary_slip: FrappeSalarySlip) -> Decimal:
	posting_date = _date(salary_slip.posting_date)
	values = frappe.get_all(
		"Salary Slip",
		filters={
			"employee": salary_slip.employee,
			"docstatus": 1,
			"name": ("!=", salary_slip.name),
			"posting_date": ("between", (posting_date.replace(month=1, day=1), posting_date)),
		},
		pluck=SLIP_WAGES_FIELD,
	)
	return sum((_decimal(value) for value in values), Decimal("0"))


def _date(value: date | str) -> date:
	return value if isinstance(value, date) else date.fromisoformat(value)


def _decimal(value: str | int | float | None) -> Decimal:
	return Decimal(str(value or 0))
