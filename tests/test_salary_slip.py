import unittest
from types import SimpleNamespace

from frappe_us_payroll.payroll.salary_slip import set_deduction_amount

TEST_AMOUNT = 12.34
TEST_COMPONENT = "US Payroll Smoke Test"


class FakeSalarySlip:
	def __init__(self, deductions):
		self.deductions = deductions

	def get(self, fieldname):
		return getattr(self, fieldname)


class ApplyUSPayrollDeductionsTest(unittest.TestCase):
	def test_sets_existing_component_to_calculated_amount(self):
		deduction = SimpleNamespace(
			salary_component=TEST_COMPONENT,
			amount=0,
			default_amount=0,
		)

		found = set_deduction_amount(FakeSalarySlip([deduction]), TEST_COMPONENT, TEST_AMOUNT)

		self.assertTrue(found)
		self.assertEqual(deduction.amount, TEST_AMOUNT)
		self.assertEqual(deduction.default_amount, TEST_AMOUNT)

	def test_does_not_add_or_change_unrelated_deductions(self):
		deduction = SimpleNamespace(
			salary_component="Unrelated Deduction",
			amount=7.89,
			default_amount=7.89,
		)
		salary_slip = FakeSalarySlip([deduction])

		found = set_deduction_amount(salary_slip, TEST_COMPONENT, TEST_AMOUNT)

		self.assertFalse(found)
		self.assertEqual(deduction.amount, 7.89)
		self.assertEqual(deduction.default_amount, 7.89)
		self.assertEqual(len(salary_slip.deductions), 1)


if __name__ == "__main__":
	unittest.main()
