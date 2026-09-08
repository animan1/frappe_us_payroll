from datetime import date
from decimal import Decimal
from typing import Protocol, cast

import frappe

from frappe_us_payroll.custom_fields import W4_FILING_STATUSES
from frappe_us_payroll.federal.income_tax import FilingStatus, FormW4
from frappe_us_payroll.payroll.components import MissingSalaryComponentError
from frappe_us_payroll.payroll.income_tax import apply_federal_income_tax_withholding
from frappe_us_payroll.payroll.social_security import (
	SocialSecuritySalarySlip,
	apply_social_security_withholding,
	taxable_wages,
)

OPENING_WAGES_FIELD = "us_social_security_taxable_wages_till_date"
SLIP_WAGES_FIELD = "us_social_security_taxable_wages"


class SalaryStructureAssignment(Protocol):
	def get(self, fieldname: str) -> str | int | float | None: ...


class FrappeSalarySlip(SocialSecuritySalarySlip, Protocol):
	name: str
	employee: str
	payroll_frequency: str
	_salary_structure_assignment: SalaryStructureAssignment


def apply_us_payroll_deductions(salary_slip: FrappeSalarySlip) -> None:
	"""Apply supported US deductions through HRMS's regional extension point."""
	try:
		taxable_components = _taxable_social_security_components()
		current_taxable_wages = taxable_wages(salary_slip.earnings, taxable_components)
		apply_social_security_withholding(
			salary_slip,
			taxable_components=taxable_components,
			prior_taxable_wages=_prior_social_security_wages(salary_slip),
			opening_taxable_wages=_decimal(salary_slip._salary_structure_assignment.get(OPENING_WAGES_FIELD)),
		)
		apply_federal_income_tax_withholding(
			salary_slip,
			taxable_wages=current_taxable_wages,
			form_w4=_employee_w4(salary_slip.employee),
		)
	except MissingSalaryComponentError as error:
		frappe.throw(str(error), exc=frappe.ValidationError, title="US Payroll Configuration Required")


def _employee_w4(employee_name: str) -> FormW4:
	employee = frappe.get_doc("Employee", employee_name)
	filing_status = employee.get("us_w4_filing_status")
	if not isinstance(filing_status, str) or filing_status not in W4_FILING_STATUSES:
		frappe.throw(
			"Set the employee's W-4 filing status before calculating payroll.",
			exc=frappe.ValidationError,
			title="W-4 Filing Status Required",
		)
	return FormW4(
		filing_status=cast(FilingStatus, W4_FILING_STATUSES[filing_status]),
		multiple_jobs=bool(employee.get("us_w4_step_2")),
		dependents_amount=_decimal(employee.get("us_w4_dependents_amount")),
		other_income=_decimal(employee.get("us_w4_other_income")),
		deductions=_decimal(employee.get("us_w4_deductions")),
		extra_withholding=_decimal(employee.get("us_w4_extra_withholding")),
	)


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
