import unittest
from decimal import Decimal

from frappe_us_payroll.federal.income_tax import FormW4, calculate_federal_income_tax_withholding


class FederalIncomeTaxTest(unittest.TestCase):
	def test_2026_single_biweekly_withholding(self) -> None:
		withholding = calculate_federal_income_tax_withholding(
			taxable_wages=Decimal("1000.00"),
			pay_frequency="biweekly",
			form_w4=FormW4(filing_status="single"),
			tax_year=2026,
		)

		self.assertEqual(withholding, Decimal("38.08"))

	def test_applies_all_current_form_w4_adjustments(self) -> None:
		withholding = calculate_federal_income_tax_withholding(
			taxable_wages=Decimal("2000.00"),
			pay_frequency="biweekly",
			form_w4=FormW4(
				filing_status="married",
				multiple_jobs=True,
				dependents_amount=Decimal("2000.00"),
				other_income=Decimal("1000.00"),
				deductions=Decimal("500.00"),
				extra_withholding=Decimal("10.00"),
			),
			tax_year=2026,
		)

		self.assertEqual(withholding, Decimal("91.54"))


if __name__ == "__main__":
	unittest.main()
