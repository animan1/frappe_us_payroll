from datetime import date, datetime
from typing import Protocol

from frappe_us_payroll.payroll.components import SalarySlipComponents, SalarySlipEarnings


class SalaryStructureAssignment(Protocol):
	def get(self, fieldname: str) -> str | int | float | None: ...


class SocialSecuritySalarySlip(SalarySlipComponents, SalarySlipEarnings, Protocol):
	posting_date: date | datetime | str
	us_social_security_taxable_wages: float


class FederalIncomeTaxSalarySlip(SalarySlipComponents, Protocol):
	payroll_frequency: str
	posting_date: date | datetime | str


class MedicareSalarySlip(SalarySlipComponents, Protocol):
	us_medicare_taxable_wages: float


class FutaSalarySlip(SalarySlipComponents, Protocol):
	us_futa_taxable_wages: float


class FrappeSalarySlip(
	SocialSecuritySalarySlip,
	FederalIncomeTaxSalarySlip,
	MedicareSalarySlip,
	FutaSalarySlip,
	Protocol,
):
	name: str
	employee: str
	_salary_structure_assignment: SalaryStructureAssignment
