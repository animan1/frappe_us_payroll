import unittest
from decimal import Decimal

from frappe_us_payroll.washington.rules import (
	calculate_cares,
	calculate_industrial_insurance,
	calculate_paid_leave,
	calculate_unemployment,
)


class WashingtonRulesTest(unittest.TestCase):
	def test_paid_leave_uses_2026_employee_and_employer_shares(self) -> None:
		liability = calculate_paid_leave(
			covered_wages=Decimal("1000"),
			prior_covered_wages=Decimal("0"),
			tax_year=2026,
			employer_share_required=True,
		)

		self.assertEqual(liability.employee, Decimal("8.07"))
		self.assertEqual(liability.employer, Decimal("3.23"))

	def test_paid_leave_caps_current_wages_at_the_annual_base(self) -> None:
		liability = calculate_paid_leave(
			covered_wages=Decimal("1000"),
			prior_covered_wages=Decimal("184000"),
			tax_year=2026,
			employer_share_required=False,
		)

		self.assertEqual(liability.employee, Decimal("4.04"))
		self.assertEqual(liability.employer, Decimal("0.00"))

	def test_cares_has_no_social_security_wage_cap(self) -> None:
		self.assertEqual(
			calculate_cares(covered_wages=Decimal("200000"), tax_year=2026),
			Decimal("1160.00"),
		)

	def test_unemployment_uses_configured_rate_and_annual_base(self) -> None:
		self.assertEqual(
			calculate_unemployment(
				taxable_wages=Decimal("1000"),
				prior_taxable_wages=Decimal("78000"),
				tax_year=2026,
				employer_rate=Decimal("0.012"),
			),
			Decimal("2.40"),
		)

	def test_industrial_insurance_uses_separate_hourly_rates(self) -> None:
		self.assertEqual(
			calculate_industrial_insurance(
				hours=Decimal("80"),
				employee_rate_per_hour=Decimal("0.1755"),
				employer_rate_per_hour=Decimal("0.4046"),
			),
			(Decimal("14.04"), Decimal("32.37")),
		)

	def test_unknown_year_fails_closed(self) -> None:
		with self.assertRaisesRegex(ValueError, "not available for 2027"):
			calculate_cares(covered_wages=Decimal("1000"), tax_year=2027)


if __name__ == "__main__":
	unittest.main()
