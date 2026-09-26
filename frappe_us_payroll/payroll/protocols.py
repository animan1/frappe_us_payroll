from collections.abc import Iterable
from datetime import date, datetime
from typing import Protocol

from frappe_us_payroll.payroll.components import SalarySlipComponents, SalarySlipEarnings
from frappe_us_payroll.washington.salary_slip import WashingtonSalarySlip


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
	WashingtonSalarySlip,
	Protocol,
):
	name: str
	employee: str
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
