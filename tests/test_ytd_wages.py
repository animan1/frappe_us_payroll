import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from frappe_us_payroll.payroll.ytd import prior_taxable_wages


class PriorTaxableWagesTest(unittest.TestCase):
	def test_sums_taxable_earning_rows_from_submitted_slips(self) -> None:
		get_all = MagicMock()
		get_all.side_effect = [["SAL-0001", "TIMETREX-YTD-2026-HR-EMP-00001"], [1000.0, 250.25]]

		result = prior_taxable_wages(
			get_all=get_all,
			employee="HR-EMP-00001",
			current_slip="SAL-0002",
			posting_date="2026-09-01",
			taxable_components={"Basic", "Tips"},
		)

		self.assertEqual(result, Decimal("1250.25"))
		self.assertEqual(get_all.call_args_list[1].args, ("Salary Detail",))
		self.assertEqual(get_all.call_args_list[1].kwargs["filters"]["parentfield"], "earnings")

	def test_returns_zero_without_prior_slips(self) -> None:
		get_all = MagicMock(return_value=[])
		get_all.return_value = []

		result = prior_taxable_wages(
			get_all=get_all,
			employee="HR-EMP-00001",
			current_slip="SAL-0001",
			posting_date="2026-01-15",
			taxable_components={"Basic"},
		)

		self.assertEqual(result, Decimal("0.00"))
		self.assertEqual(get_all.call_count, 1)


if __name__ == "__main__":
	unittest.main()
