import unittest
from decimal import Decimal

from frappe_us_payroll.federal.social_security import calculate_social_security_withholding


class SocialSecurityCalculationTest(unittest.TestCase):
	def test_calculates_employee_withholding(self) -> None:
		withholding = calculate_social_security_withholding(
			taxable_wages=Decimal("1000.00"),
			prior_taxable_wages=Decimal("0.00"),
			tax_year=2026,
		)

		self.assertEqual(withholding, Decimal("62.00"))

	def test_caps_2026_tax_at_the_authoritative_wage_base(self) -> None:
		withholding = calculate_social_security_withholding(
			taxable_wages=Decimal("184500.00"),
			prior_taxable_wages=Decimal("0.00"),
			tax_year=2026,
		)

		self.assertEqual(withholding, Decimal("11439.00"))

	def test_taxes_only_wages_remaining_below_the_2026_limit(self) -> None:
		withholding = calculate_social_security_withholding(
			taxable_wages=Decimal("1000.00"),
			prior_taxable_wages=Decimal("184000.00"),
			tax_year=2026,
		)

		self.assertEqual(withholding, Decimal("31.00"))

	def test_withholds_nothing_after_the_2026_limit(self) -> None:
		withholding = calculate_social_security_withholding(
			taxable_wages=Decimal("1000.00"),
			prior_taxable_wages=Decimal("184500.00"),
			tax_year=2026,
		)

		self.assertEqual(withholding, Decimal("0.00"))
