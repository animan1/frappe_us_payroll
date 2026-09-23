import unittest
from decimal import Decimal

from frappe_us_payroll.federal.medicare import calculate_medicare_liability


class MedicareTest(unittest.TestCase):
	def test_employee_and_employer_standard_shares_match(self) -> None:
		liability = calculate_medicare_liability(
			taxable_wages=Decimal("1000.00"),
			prior_taxable_wages=Decimal("0.00"),
		)

		self.assertEqual(liability.standard_employee, Decimal("14.50"))
		self.assertEqual(liability.total_employee, Decimal("14.50"))
		self.assertEqual(liability.employer, Decimal("14.50"))
		self.assertEqual(liability.additional_employee, Decimal("0.00"))

	def test_additional_medicare_applies_only_above_200000(self) -> None:
		liability = calculate_medicare_liability(
			taxable_wages=Decimal("2000.00"),
			prior_taxable_wages=Decimal("199000.00"),
		)

		self.assertEqual(liability.standard_employee, Decimal("29.00"))
		self.assertEqual(liability.total_employee, Decimal("38.00"))
		self.assertEqual(liability.employer, Decimal("29.00"))
		self.assertEqual(liability.additional_employee, Decimal("9.00"))

	def test_additional_medicare_has_no_employer_match(self) -> None:
		liability = calculate_medicare_liability(
			taxable_wages=Decimal("1000.00"),
			prior_taxable_wages=Decimal("200000.00"),
		)

		self.assertEqual(liability.standard_employee, Decimal("14.50"))
		self.assertEqual(liability.total_employee, Decimal("23.50"))
		self.assertEqual(liability.employer, Decimal("14.50"))


if __name__ == "__main__":
	unittest.main()
