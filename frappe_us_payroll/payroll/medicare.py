from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from frappe_us_payroll.federal.medicare import MedicareLiability, calculate_medicare_liability
from frappe_us_payroll.payroll.component_names import MEDICARE_EMPLOYEE, MEDICARE_EMPLOYER
from frappe_us_payroll.payroll.components import (
	DEDUCTIONS,
	EMPLOYER_CONTRIBUTIONS,
	SalarySlipComponents,
	as_frappe_currency,
	set_component_amount,
)

MEDICARE_EMPLOYEE_COMPONENT = MEDICARE_EMPLOYEE
MEDICARE_EMPLOYER_COMPONENT = MEDICARE_EMPLOYER


class MedicareSalarySlip(SalarySlipComponents, Protocol):
	posting_date: date | datetime | str
	us_medicare_taxable_wages: float


def apply_medicare_liability(
	salary_slip: MedicareSalarySlip,
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
) -> MedicareLiability:
	liability = calculate_medicare_liability(
		taxable_wages=taxable_wages,
		prior_taxable_wages=prior_taxable_wages,
	)
	salary_slip.us_medicare_taxable_wages = as_frappe_currency(taxable_wages)
	set_component_amount(salary_slip, DEDUCTIONS, MEDICARE_EMPLOYEE_COMPONENT, liability.employee)
	set_component_amount(
		salary_slip,
		EMPLOYER_CONTRIBUTIONS,
		MEDICARE_EMPLOYER_COMPONENT,
		liability.employer,
	)
	return liability
