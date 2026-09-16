from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

from frappe_us_payroll.federal.futa import calculate_futa_liability
from frappe_us_payroll.payroll.component_names import FUTA_EMPLOYER
from frappe_us_payroll.payroll.components import (
	EMPLOYER_CONTRIBUTIONS,
	SalarySlipComponents,
	as_frappe_currency,
	set_component_amount,
)

FUTA_COMPONENT = FUTA_EMPLOYER


class FutaSalarySlip(SalarySlipComponents, Protocol):
	posting_date: date | datetime | str
	us_futa_taxable_wages: float


def apply_futa_liability(
	salary_slip: FutaSalarySlip,
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
	tax_year: int,
) -> Decimal:
	liability = calculate_futa_liability(
		taxable_wages=taxable_wages,
		prior_taxable_wages=prior_taxable_wages,
		tax_year=tax_year,
	)
	salary_slip.us_futa_taxable_wages = as_frappe_currency(taxable_wages)
	set_component_amount(salary_slip, EMPLOYER_CONTRIBUTIONS, FUTA_COMPONENT, liability)
	return liability
