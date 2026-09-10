import unittest
from collections.abc import Iterable, Mapping
from decimal import Decimal

from frappe_us_payroll.payroll.component_names import (
	WA_CARES_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYER,
	WA_PAID_LEAVE_EMPLOYEE,
	WA_PAID_LEAVE_EMPLOYER,
	WA_UNEMPLOYMENT_EMPLOYER,
)
from frappe_us_payroll.payroll.components import SalaryComponentRow
from frappe_us_payroll.washington.salary_slip import (
	WashingtonPayrollConfiguration,
	apply_washington_payroll,
)


class FakeComponent:
	def __init__(self, name: str) -> None:
		self.salary_component = name
		self.amount = 0.0
		self.default_amount = 0.0
		self.amount_based_on_formula = 1
		self.formula = "old formula"


class FakeSalarySlip:
	def __init__(self) -> None:
		self.wa_paid_leave_taxable_wages = 0.0
		self.wa_unemployment_taxable_wages = 0.0
		self.deductions: list[SalaryComponentRow] = [
			FakeComponent(WA_PAID_LEAVE_EMPLOYEE),
			FakeComponent(WA_CARES_EMPLOYEE),
			FakeComponent(WA_INDUSTRIAL_INSURANCE_EMPLOYEE),
		]
		self._evaluated_components: Mapping[str, Iterable[SalaryComponentRow]] = {
			"employer_contributions": [
				FakeComponent(WA_PAID_LEAVE_EMPLOYER),
				FakeComponent(WA_INDUSTRIAL_INSURANCE_EMPLOYER),
				FakeComponent(WA_UNEMPLOYMENT_EMPLOYER),
			]
		}

	def get(self, fieldname: str) -> Iterable[SalaryComponentRow] | None:
		return self.deductions if fieldname == "deductions" else None


class WashingtonSalarySlipTest(unittest.TestCase):
	def test_maps_employee_and_employer_liabilities(self) -> None:
		slip = FakeSalarySlip()
		apply_washington_payroll(
			slip,
			configuration=WashingtonPayrollConfiguration(
				paid_leave_exempt=False,
				cares_exempt=False,
				paid_leave_employer_share_required=True,
				unemployment_rate=Decimal("0.012"),
				industrial_insurance_employee_rate=Decimal("0.1755"),
				industrial_insurance_employer_rate=Decimal("0.4046"),
			),
			tax_year=2026,
			paid_leave_wages=Decimal("1000"),
			prior_paid_leave_wages=Decimal("0"),
			unemployment_wages=Decimal("1000"),
			prior_unemployment_wages=Decimal("0"),
			hours=Decimal("80"),
		)

		deductions = {row.salary_component: row.amount for row in slip.deductions}
		contributions = {
			row.salary_component: row.amount for row in slip._evaluated_components["employer_contributions"]
		}
		self.assertEqual(deductions[WA_PAID_LEAVE_EMPLOYEE], 8.07)
		self.assertEqual(deductions[WA_CARES_EMPLOYEE], 5.8)
		self.assertEqual(deductions[WA_INDUSTRIAL_INSURANCE_EMPLOYEE], 14.04)
		self.assertEqual(contributions[WA_PAID_LEAVE_EMPLOYER], 3.23)
		self.assertEqual(contributions[WA_INDUSTRIAL_INSURANCE_EMPLOYER], 32.37)
		self.assertEqual(contributions[WA_UNEMPLOYMENT_EMPLOYER], 12)

	def test_employee_exemptions_zero_only_covered_programs(self) -> None:
		slip = FakeSalarySlip()
		apply_washington_payroll(
			slip,
			configuration=WashingtonPayrollConfiguration(
				paid_leave_exempt=True,
				cares_exempt=True,
				paid_leave_employer_share_required=False,
				unemployment_rate=Decimal("0"),
				industrial_insurance_employee_rate=Decimal("0"),
				industrial_insurance_employer_rate=Decimal("0"),
			),
			tax_year=2026,
			paid_leave_wages=Decimal("1000"),
			prior_paid_leave_wages=Decimal("0"),
			unemployment_wages=Decimal("0"),
			prior_unemployment_wages=Decimal("0"),
			hours=Decimal("0"),
		)

		self.assertTrue(all(row.amount == 0 for row in slip.deductions))
		self.assertEqual(slip.wa_paid_leave_taxable_wages, 0)
