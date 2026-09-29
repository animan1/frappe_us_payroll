import unittest
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from frappe_us_payroll.payroll.components import (
	DEDUCTIONS,
	EMPLOYER_CONTRIBUTIONS,
	MissingSalaryComponentError,
	SalaryComponentRow,
	set_component_amount,
)

TEST_AMOUNT = Decimal("12.34")
TEST_COMPONENT = "US Payroll Smoke Test"


@dataclass
class FakeDeduction:
	salary_component: str
	amount: float
	default_amount: float
	amount_based_on_formula: int = 0
	formula: str | None = None


class FakeSalarySlip:
	def __init__(
		self,
		deductions: list[FakeDeduction],
		evaluated_components: dict[str, list[FakeDeduction]] | None = None,
	) -> None:
		self.deductions = deductions
		self._evaluated_components: Mapping[str, Iterable[SalaryComponentRow]] = evaluated_components or {}

	def get(self, fieldname: str) -> Iterable[SalaryComponentRow] | None:
		return self.deductions if fieldname == "deductions" else None


class ApplyUSPayrollDeductionsTest(unittest.TestCase):
	def test_sets_existing_component_to_calculated_amount(self) -> None:
		deduction = FakeDeduction(
			salary_component=TEST_COMPONENT,
			amount=0,
			default_amount=0,
		)

		set_component_amount(FakeSalarySlip([deduction]), DEDUCTIONS, TEST_COMPONENT, TEST_AMOUNT)

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
			set_component_amount(salary_slip, DEDUCTIONS, TEST_COMPONENT, TEST_AMOUNT)

		self.assertEqual(deduction.amount, 7.89)
		self.assertEqual(deduction.default_amount, 7.89)
		self.assertEqual(len(salary_slip.deductions), 1)

	def test_sets_component_awaiting_hrms_evaluation(self) -> None:
		contribution = FakeDeduction(TEST_COMPONENT, 0, 0, 1, "base * 0.10")
		salary_slip = FakeSalarySlip([], {EMPLOYER_CONTRIBUTIONS: [contribution]})

		set_component_amount(
			salary_slip,
			EMPLOYER_CONTRIBUTIONS,
			TEST_COMPONENT,
			TEST_AMOUNT,
		)

		self.assertEqual(contribution.amount, 12.34)
		self.assertEqual(contribution.default_amount, 12.34)
		self.assertEqual(contribution.amount_based_on_formula, 0)
		self.assertIsNone(contribution.formula)

	def test_finds_evaluated_component_when_loaded_table_is_partial(self) -> None:
		loaded_component = FakeDeduction("Other Component", 7.89, 7.89)
		evaluated_component = FakeDeduction(TEST_COMPONENT, 0, 0, 1, "base * 0.10")
		salary_slip = FakeSalarySlip(
			[loaded_component],
			{DEDUCTIONS: [evaluated_component]},
		)

		set_component_amount(salary_slip, DEDUCTIONS, TEST_COMPONENT, TEST_AMOUNT)

		self.assertEqual(loaded_component.amount, 7.89)
		self.assertEqual(evaluated_component.amount, 12.34)
		self.assertEqual(evaluated_component.default_amount, 12.34)
		self.assertEqual(evaluated_component.amount_based_on_formula, 0)
		self.assertIsNone(evaluated_component.formula)


if __name__ == "__main__":
	unittest.main()
