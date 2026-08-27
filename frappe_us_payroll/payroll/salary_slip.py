from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol, cast

from python_taxes.federal import income

import frappe

from frappe_us_payroll.custom_fields import FILING_STATUS
from frappe_us_payroll.federal.social_security import CENT
from frappe_us_payroll.payroll.components import (
	DEDUCTIONS,
	EMPLOYER_CONTRIBUTIONS,
	MissingSalaryComponentError,
	as_frappe_currency,
	set_component_amount,
)
from frappe_us_payroll.payroll.social_security import (
	SocialSecuritySalarySlip,
	_posting_date,
	apply_social_security_withholding,
	taxable_wages,
)

OPENING_WAGES_FIELD = "us_social_security_taxable_wages_till_date"
SLIP_WAGES_FIELD = "us_social_security_taxable_wages"
FIT_COMPONENT = "US - Federal Income Tax"


class SalaryStructureAssignment(Protocol):
	def get(self, fieldname: str) -> str | int | float | None: ...


class FrappeSalarySlip(SocialSecuritySalarySlip, Protocol):
	name: str
	employee: str
	_salary_structure_assignment: SalaryStructureAssignment


def apply_us_payroll_deductions(salary_slip: FrappeSalarySlip) -> None:
	"""Apply supported US deductions through HRMS's regional extension point."""
	try:
		prior_taxable_wages = _prior_social_security_wages(salary_slip)
		opening_taxable_wages = _decimal(salary_slip._salary_structure_assignment.get(OPENING_WAGES_FIELD))
		taxable_components = _taxable_social_security_components()
		current_taxable_wages = taxable_wages(salary_slip.earnings, taxable_components).quantize(
			CENT, rounding=ROUND_HALF_UP
		)
		apply_social_security_withholding(
			salary_slip,
			taxable_components=taxable_components,
			prior_taxable_wages=prior_taxable_wages,
			opening_taxable_wages=opening_taxable_wages,
			deduction=True,
		)
		_apply_fit_withholding(salary_slip, current_taxable_wages)
		_apply_futa_calculation(
			salary_slip, prior_taxable_wages + opening_taxable_wages, current_taxable_wages
		)
	except MissingSalaryComponentError as error:
		frappe.throw(str(error), exc=frappe.ValidationError, title="US Payroll Configuration Required")


def _apply_futa_calculation(
	salary_slip: SocialSecuritySalarySlip, prior_taxable_wages: Decimal, current_taxable_wages
):
	remaining_wage_base = max(Decimal("7000") - prior_taxable_wages, Decimal("0"))
	futa_wages = min(current_taxable_wages, remaining_wage_base)
	futa = (futa_wages * Decimal("0.006")).quantize(
		CENT,
		rounding=ROUND_HALF_UP,
	)
	salary_slip.futa_calculated = as_frappe_currency(futa)


def apply_us_employer_contributions(salary_slip):
	# prior_taxable_wages = _prior_social_security_wages(salary_slip)
	# opening_taxable_wages = _decimal(salary_slip._salary_structure_assignment.get(OPENING_WAGES_FIELD))
	# apply_social_security_withholding(
	# 	salary_slip,
	# 	taxable_components=_taxable_social_security_components(),
	# 	prior_taxable_wages=prior_taxable_wages,
	# 	opening_taxable_wages=opening_taxable_wages,
	# 	deduction=False,
	# )
	pass


def _apply_fit_withholding(salary_slip: SocialSecuritySalarySlip, current_taxable_wages) -> Decimal:
	employee = frappe.get_doc("Employee", salary_slip.employee)
	filing_status = FILING_STATUS[employee.us_w4_filing_status]
	if not filing_status:
		frappe.throw(
			"Filing status not set for employee", exc=frappe.ValidationError, title="Filing Status Required"
		)
	withholding = income.employer_withholding(
		taxable_wages=current_taxable_wages,
		# FIXME
		pay_frequency="biweekly",
		filing_status=filing_status,
		multiple_jobs=bool(employee.us_w4_step_2),
		tax_credits=_decimal(employee.us_w4_dependents_amount or 0),
		other_income=_decimal(employee.us_w4_other_income or 0),
		deductions=_decimal(employee.us_w4_deductions or 0),
		extra_withholding=_decimal(employee.us_w4_extra_withholding or 0),
		tax_year=_posting_date(salary_slip.posting_date).year,
		rounded=False,
	)

	set_component_amount(salary_slip, DEDUCTIONS, FIT_COMPONENT, withholding)
	return withholding


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


@frappe.whitelist()
def recalculate(salary_slip):
	if isinstance(salary_slip, str):
		salary_slip = frappe.parse_json(salary_slip)

	doc = frappe.get_doc(salary_slip)

	apply_us_payroll_deductions(doc)

	return {"deductions": [row.as_dict() for row in doc.deductions]}
