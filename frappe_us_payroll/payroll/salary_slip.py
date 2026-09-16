from decimal import Decimal
from typing import Protocol, cast

import frappe

from frappe_us_payroll.custom_fields import W4_FILING_STATUSES
from frappe_us_payroll.federal.income_tax import FilingStatus, FormW4
from frappe_us_payroll.payroll.components import MissingSalaryComponentError
from frappe_us_payroll.payroll.dates import as_date
from frappe_us_payroll.payroll.futa import FutaSalarySlip, apply_futa_liability
from frappe_us_payroll.payroll.income_tax import apply_federal_income_tax_withholding
from frappe_us_payroll.payroll.medicare import MedicareSalarySlip, apply_medicare_liability
from frappe_us_payroll.payroll.social_security import (
	SocialSecuritySalarySlip,
	apply_social_security_withholding,
	taxable_wages,
)
from frappe_us_payroll.payroll.ytd import GetAll, prior_taxable_wages


class FrappeSalarySlip(SocialSecuritySalarySlip, MedicareSalarySlip, FutaSalarySlip, Protocol):
	name: str
	employee: str
	payroll_frequency: str


def apply_us_payroll_deductions(salary_slip: FrappeSalarySlip) -> None:
	"""Apply supported US deductions through HRMS's regional extension point."""
	try:
		social_security_components = _taxable_components("us_social_security_taxable")
		prior_social_security_wages = _prior_taxable_wages(salary_slip, social_security_components)
		apply_social_security_withholding(
			salary_slip,
			taxable_components=social_security_components,
			prior_taxable_wages=prior_social_security_wages,
			opening_taxable_wages=Decimal("0.00"),
		)
		income_tax_components = _taxable_components("us_federal_income_taxable")
		apply_federal_income_tax_withholding(
			salary_slip,
			taxable_wages=taxable_wages(salary_slip.earnings, income_tax_components),
			form_w4=_employee_w4(salary_slip.employee),
		)
		medicare_components = _taxable_components("us_medicare_taxable")
		apply_medicare_liability(
			salary_slip,
			taxable_wages=taxable_wages(salary_slip.earnings, medicare_components),
			prior_taxable_wages=_prior_taxable_wages(salary_slip, medicare_components),
		)
		futa_components = _taxable_components("us_futa_taxable")
		apply_futa_liability(
			salary_slip,
			taxable_wages=taxable_wages(salary_slip.earnings, futa_components),
			prior_taxable_wages=_prior_taxable_wages(salary_slip, futa_components),
			tax_year=as_date(salary_slip.posting_date).year,
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


def _taxable_components(fieldname: str) -> set[str]:
	values = frappe.get_all(
		"Salary Component",
		filters={"type": "Earning", "disabled": 0, fieldname: 1},
		pluck="name",
	)
	return set(cast(list[str], values))


def _prior_taxable_wages(salary_slip: FrappeSalarySlip, components: set[str]) -> Decimal:
	return prior_taxable_wages(
		get_all=cast(GetAll, frappe.get_all),
		employee=salary_slip.employee,
		current_slip=salary_slip.name,
		posting_date=salary_slip.posting_date,
		taxable_components=components,
	)


def _decimal(value: str | int | float | None) -> Decimal:
	return Decimal(str(value or 0))
