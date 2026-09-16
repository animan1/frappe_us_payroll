import unittest
from decimal import Decimal

from frappe_us_payroll.federal.futa import calculate_futa_liability


class FutaTest(unittest.TestCase):
	def test_2026_liability_uses_effective_rate_after_maximum_credit(self) -> None:
		liability = calculate_futa_liability(
			taxable_wages=Decimal("1000.00"),
			prior_taxable_wages=Decimal("0.00"),
			tax_year=2026,
		)

		self.assertEqual(liability, Decimal("6.00"))

	def test_tax_applies_only_to_first_7000(self) -> None:
		liability = calculate_futa_liability(
			taxable_wages=Decimal("1000.00"),
			prior_taxable_wages=Decimal("6500.00"),
			tax_year=2026,
		)

		self.assertEqual(liability, Decimal("3.00"))

	def test_rejects_unsupported_tax_year(self) -> None:
		with self.assertRaisesRegex(ValueError, "2027"):
			calculate_futa_liability(
				taxable_wages=Decimal("1000.00"),
				prior_taxable_wages=Decimal("0.00"),
				tax_year=2027,
			)


if __name__ == "__main__":
	unittest.main()
