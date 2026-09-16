from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from frappe_us_payroll.payroll.component_names import (
	WA_CARES_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYER,
	WA_PAID_LEAVE_EMPLOYEE,
	WA_PAID_LEAVE_EMPLOYER,
	WA_UNEMPLOYMENT_EMPLOYER,
)
from frappe_us_payroll.payroll.components import (
	DEDUCTIONS,
	EMPLOYER_CONTRIBUTIONS,
	SalarySlipComponents,
	as_frappe_currency,
	set_component_amount,
)
from frappe_us_payroll.washington.rules import (
	calculate_cares,
	calculate_industrial_insurance,
	calculate_paid_leave,
	calculate_unemployment,
)


@dataclass(frozen=True)
class WashingtonPayrollConfiguration:
	paid_leave_exempt: bool
	cares_exempt: bool
	paid_leave_employer_share_required: bool
	unemployment_rate: Decimal
	industrial_insurance_employee_rate: Decimal
	industrial_insurance_employer_rate: Decimal


class WashingtonSalarySlip(SalarySlipComponents, Protocol):
	wa_paid_leave_taxable_wages: float
	wa_unemployment_taxable_wages: float


def apply_washington_payroll(
	salary_slip: WashingtonSalarySlip,
	*,
	configuration: WashingtonPayrollConfiguration,
	tax_year: int,
	paid_leave_wages: Decimal,
	prior_paid_leave_wages: Decimal,
	unemployment_wages: Decimal,
	prior_unemployment_wages: Decimal,
	hours: Decimal,
) -> None:
	"""Calculate and map supported Washington payroll items onto a Salary Slip."""
	covered_paid_leave_wages = Decimal("0") if configuration.paid_leave_exempt else paid_leave_wages
	paid_leave = calculate_paid_leave(
		taxable_wages=covered_paid_leave_wages,
		prior_taxable_wages=prior_paid_leave_wages,
		tax_year=tax_year,
		employer_share_required=configuration.paid_leave_employer_share_required,
	)
	cares = (
		Decimal("0")
		if configuration.cares_exempt
		else calculate_cares(taxable_wages=paid_leave_wages, tax_year=tax_year)
	)
	industrial_insurance_employee, industrial_insurance_employer = calculate_industrial_insurance(
		hours=hours,
		employee_rate_per_hour=configuration.industrial_insurance_employee_rate,
		employer_rate_per_hour=configuration.industrial_insurance_employer_rate,
	)
	unemployment = calculate_unemployment(
		taxable_wages=unemployment_wages,
		prior_taxable_wages=prior_unemployment_wages,
		tax_year=tax_year,
		employer_rate=configuration.unemployment_rate,
	)

	salary_slip.wa_paid_leave_taxable_wages = as_frappe_currency(covered_paid_leave_wages)
	salary_slip.wa_unemployment_taxable_wages = as_frappe_currency(unemployment_wages)
	set_component_amount(salary_slip, DEDUCTIONS, WA_PAID_LEAVE_EMPLOYEE, paid_leave.employee)
	set_component_amount(salary_slip, DEDUCTIONS, WA_CARES_EMPLOYEE, cares)
	set_component_amount(
		salary_slip, DEDUCTIONS, WA_INDUSTRIAL_INSURANCE_EMPLOYEE, industrial_insurance_employee
	)
	set_component_amount(salary_slip, EMPLOYER_CONTRIBUTIONS, WA_PAID_LEAVE_EMPLOYER, paid_leave.employer)
	set_component_amount(
		salary_slip,
		EMPLOYER_CONTRIBUTIONS,
		WA_INDUSTRIAL_INSURANCE_EMPLOYER,
		industrial_insurance_employer,
	)
	set_component_amount(salary_slip, EMPLOYER_CONTRIBUTIONS, WA_UNEMPLOYMENT_EMPLOYER, unemployment)
