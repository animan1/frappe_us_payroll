from decimal import Decimal
from typing import cast

import frappe

from frappe_us_payroll.payroll.dates import as_date
from frappe_us_payroll.payroll.protocols import FrappeSalarySlip
from frappe_us_payroll.payroll.social_security import taxable_wages
from frappe_us_payroll.payroll.ytd import GetAll, prior_taxable_wages
from frappe_us_payroll.washington.salary_slip import (
	WashingtonPayrollConfiguration,
)
from frappe_us_payroll.washington.salary_slip import (
	apply_washington_payroll as apply_calculated_washington_payroll,
)


def apply_washington_payroll(salary_slip: FrappeSalarySlip) -> None:
	"""Load Washington configuration and YTD wages, then calculate the Salary Slip."""
	paid_leave_components = _taxable_components("wa_paid_leave_taxable")
	unemployment_components = _taxable_components("wa_unemployment_taxable")
	assignment = salary_slip._salary_structure_assignment
	employee = frappe.get_doc("Employee", salary_slip.employee)
	apply_calculated_washington_payroll(
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
) -> Decimal:
	return prior_taxable_wages(
		get_all=cast(GetAll, frappe.get_all),
		employee=salary_slip.employee,
		current_slip=salary_slip.name,
		posting_date=salary_slip.posting_date,
		taxable_components=components,
	)


def _decimal(value: str | int | float | None) -> Decimal:
	return Decimal(str(value or 0))
