import unittest
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from frappe_us_payroll.payroll.components import (
	DeductionRow,
	MissingSalaryComponentError,
	set_component_amount,
)

TEST_AMOUNT = Decimal("12.34")
TEST_COMPONENT = "US Payroll Smoke Test"


@dataclass
class FakeDeduction:
	salary_component: str
	amount: float
	default_amount: float


class FakeSalarySlip:
	def __init__(self, deductions: list[FakeDeduction]) -> None:
		self.deductions = deductions

	def get(self, fieldname: str) -> Iterable[DeductionRow] | None:
		return self.deductions if fieldname == "deductions" else None


class ApplyUSPayrollDeductionsTest(unittest.TestCase):
	def test_sets_existing_component_to_calculated_amount(self) -> None:
		deduction = FakeDeduction(
			salary_component=TEST_COMPONENT,
			amount=0,
			default_amount=0,
		)

		set_component_amount(FakeSalarySlip([deduction]), TEST_COMPONENT, TEST_AMOUNT)

		self.assertEqual(deduction.amount, 12.34)
		self.assertEqual(deduction.default_amount, 12.34)

	def test_missing_component_fails_without_changing_unrelated_deductions(self) -> None:
		deduction = FakeDeduction(
			salary_component="Unrelated Deduction",
			amount=7.89,
			default_amount=7.89,
		)
		salary_slip = FakeSalarySlip([deduction])

		with self.assertRaisesRegex(MissingSalaryComponentError, TEST_COMPONENT):
			set_component_amount(salary_slip, TEST_COMPONENT, TEST_AMOUNT)

		self.assertEqual(deduction.amount, 7.89)
		self.assertEqual(deduction.default_amount, 7.89)
		self.assertEqual(len(salary_slip.deductions), 1)


if __name__ == "__main__":
	unittest.main()
