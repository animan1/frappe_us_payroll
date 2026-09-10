from decimal import Decimal
from typing import cast

import frappe

from frappe_us_payroll.custom_fields import W4_FILING_STATUSES
from frappe_us_payroll.federal.income_tax import FilingStatus, FormW4
from frappe_us_payroll.payroll.components import MissingSalaryComponentError
from frappe_us_payroll.payroll.dates import as_date
from frappe_us_payroll.payroll.futa import apply_futa_liability
from frappe_us_payroll.payroll.income_tax import apply_federal_income_tax_withholding
from frappe_us_payroll.payroll.medicare import apply_medicare_liability
from frappe_us_payroll.payroll.protocols import FrappeSalarySlip
from frappe_us_payroll.payroll.social_security import (
	apply_social_security_withholding,
	taxable_wages,
)
from frappe_us_payroll.payroll.ytd import (
	ConflictingDraftSalarySlipsError,
	GetAll,
	prior_taxable_wages,
)
from frappe_us_payroll.washington.salary_slip import (
	WashingtonPayrollConfiguration,
	apply_washington_payroll,
)

SOCIAL_SECURITY_OPENING_WAGES_FIELD = "us_social_security_taxable_wages_till_date"
MEDICARE_OPENING_WAGES_FIELD = "us_medicare_taxable_wages_till_date"
FUTA_OPENING_WAGES_FIELD = "us_futa_taxable_wages_till_date"


def apply_us_payroll_deductions(salary_slip: FrappeSalarySlip) -> None:
	"""Apply supported US deductions through HRMS's regional extension point."""
	try:
		social_security_components = _taxable_components("us_social_security_taxable")
		apply_social_security_withholding(
			salary_slip,
			taxable_components=social_security_components,
			prior_taxable_wages=_prior_taxable_wages(
				salary_slip,
				social_security_components,
				SOCIAL_SECURITY_OPENING_WAGES_FIELD,
			),
		)
		apply_federal_income_tax_withholding(
			salary_slip,
			taxable_wages=taxable_wages(
				salary_slip.earnings,
				_taxable_components("us_federal_income_taxable"),
			),
			form_w4=_employee_w4(salary_slip.employee),
		)
		medicare_components = _taxable_components("us_medicare_taxable")
		apply_medicare_liability(
			salary_slip,
			taxable_wages=taxable_wages(salary_slip.earnings, medicare_components),
			prior_taxable_wages=_prior_taxable_wages(
				salary_slip,
				medicare_components,
				MEDICARE_OPENING_WAGES_FIELD,
			),
		)
		futa_components = _taxable_components("us_futa_taxable")
		apply_futa_liability(
			salary_slip,
			taxable_wages=taxable_wages(salary_slip.earnings, futa_components),
			prior_taxable_wages=_prior_taxable_wages(
				salary_slip,
				futa_components,
				FUTA_OPENING_WAGES_FIELD,
			),
			tax_year=as_date(salary_slip.posting_date).year,
		)
		if bool(salary_slip._salary_structure_assignment.get("wa_payroll_enabled")):
			_apply_washington_payroll(salary_slip)
	except MissingSalaryComponentError as error:
		frappe.throw(str(error), exc=frappe.ValidationError, title="US Payroll Configuration Required")
	except ConflictingDraftSalarySlipsError as error:
		frappe.throw(str(error), exc=frappe.ValidationError, title="Conflicting Draft Salary Slips")


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


def _prior_taxable_wages(
	salary_slip: FrappeSalarySlip,
	components: set[str],
	opening_wages_field: str | None,
) -> Decimal:
	opening_wages = (
		_decimal(salary_slip._salary_structure_assignment.get(opening_wages_field))
		if opening_wages_field
		else Decimal("0.00")
	)
	return prior_taxable_wages(
		get_all=cast(GetAll, frappe.get_all),
		employee=salary_slip.employee,
		current_slip=salary_slip.name,
		posting_date=salary_slip.posting_date,
		taxable_components=components,
		opening_taxable_wages=opening_wages,
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
		prior_paid_leave_wages=_prior_taxable_wages(salary_slip, paid_leave_components, None),
		unemployment_wages=taxable_wages(salary_slip.earnings, unemployment_components),
		prior_unemployment_wages=_prior_taxable_wages(salary_slip, unemployment_components, None),
		hours=_decimal(salary_slip.total_working_hours),
	)


def _decimal(value: str | int | float | None) -> Decimal:
	return Decimal(str(value or 0))
