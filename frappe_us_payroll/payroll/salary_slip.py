from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol, cast

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
from frappe_us_payroll.washington.salary_slip import (
	WashingtonPayrollConfiguration,
	WashingtonSalarySlip,
	apply_washington_payroll,
)


class SalaryStructureAssignment(Protocol):
	def get(self, fieldname: str) -> str | int | float | None: ...


class FrappeSalarySlip(
	SocialSecuritySalarySlip, MedicareSalarySlip, FutaSalarySlip, WashingtonSalarySlip, Protocol
):
	name: str
	employee: str
	payroll_frequency: str
	posting_date: date | datetime | str
	total_working_hours: float
	_salary_structure_assignment: SalaryStructureAssignment


class SerializableRow(Protocol):
	def as_dict(self) -> dict[str, object]: ...


class RecalculableSalarySlip(FrappeSalarySlip, Protocol):
	deductions: Iterable[SerializableRow]
	employer_contributions: Iterable[SerializableRow]
	total_deduction: float
	base_total_deduction: float
	net_pay: float
	base_net_pay: float
	rounded_total: float
	base_rounded_total: float

	def check_permission(self, permission_type: str) -> None: ...
	def set_salary_structure_assignment(self) -> None: ...
	def set_precision_for_component_amounts(self) -> None: ...
	def set_net_pay(self) -> None: ...


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
		if bool(salary_slip._salary_structure_assignment.get("wa_payroll_enabled")):
			_apply_washington_payroll(salary_slip)
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


def _apply_washington_payroll(salary_slip: FrappeSalarySlip) -> None:
	paid_leave_components = _taxable_components("wa_paid_leave_taxable")
	unemployment_components = _taxable_components("wa_unemployment_taxable")
	assignment = salary_slip._salary_structure_assignment
	employee = frappe.get_doc("Employee", salary_slip.employee)
	apply_washington_payroll(
		salary_slip,
		configuration=WashingtonPayrollConfiguration(
			paid_leave_exempt=bool(employee.get("wa_paid_leave_exempt")),
			cares_exempt=bool(employee.get("wa_cares_exempt")),
			paid_leave_employer_share_required=bool(assignment.get("wa_pfml_employer_share_required")),
			unemployment_rate=_decimal(assignment.get("wa_unemployment_rate")) / Decimal("100"),
			industrial_insurance_employee_rate=_decimal(assignment.get("wa_li_employee_rate_per_hour")),
			industrial_insurance_employer_rate=_decimal(assignment.get("wa_li_employer_rate_per_hour")),
		),
		tax_year=as_date(salary_slip.posting_date).year,
		paid_leave_wages=taxable_wages(salary_slip.earnings, paid_leave_components),
		prior_paid_leave_wages=_prior_taxable_wages(salary_slip, paid_leave_components),
		unemployment_wages=taxable_wages(salary_slip.earnings, unemployment_components),
		prior_unemployment_wages=_prior_taxable_wages(salary_slip, unemployment_components),
		hours=_decimal(salary_slip.total_working_hours),
	)


def _decimal(value: str | int | float | None) -> Decimal:
	return Decimal(str(value or 0))


@frappe.whitelist()
def recalculate(salary_slip: str | dict[str, Any]) -> dict[str, object]:
	"""Recalculate regional rows and totals for an unsaved Salary Slip from the UI."""
	values = frappe.parse_json(salary_slip) if isinstance(salary_slip, str) else salary_slip
	doc = cast(RecalculableSalarySlip, frappe.get_doc(cast(Any, values)))
	doc.check_permission("write")
	doc.set_salary_structure_assignment()
	apply_us_payroll_deductions(doc)
	doc.set_precision_for_component_amounts()
	doc.set_net_pay()
	return {
		"deductions": [row.as_dict() for row in doc.deductions],
		"employer_contributions": [row.as_dict() for row in doc.employer_contributions],
		"us_social_security_taxable_wages": doc.us_social_security_taxable_wages,
		"us_medicare_taxable_wages": doc.us_medicare_taxable_wages,
		"us_futa_taxable_wages": doc.us_futa_taxable_wages,
		"wa_paid_leave_taxable_wages": doc.wa_paid_leave_taxable_wages,
		"wa_unemployment_taxable_wages": doc.wa_unemployment_taxable_wages,
		"total_deduction": doc.total_deduction,
		"base_total_deduction": doc.base_total_deduction,
		"net_pay": doc.net_pay,
		"base_net_pay": doc.base_net_pay,
		"rounded_total": doc.rounded_total,
		"base_rounded_total": doc.base_rounded_total,
	}
