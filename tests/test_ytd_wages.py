import unittest
from decimal import Decimal
from unittest.mock import MagicMock

from frappe_us_payroll.federal.futa import calculate_futa_liability
from frappe_us_payroll.federal.medicare import calculate_medicare_liability
from frappe_us_payroll.federal.social_security import calculate_social_security_withholding
from frappe_us_payroll.payroll.ytd import ConflictingDraftSalarySlipsError, prior_taxable_wages


class PriorTaxableWagesTest(unittest.TestCase):
	def test_sums_taxable_earning_rows_from_submitted_slips(self) -> None:
		get_all = MagicMock()
		get_all.side_effect = [
			[],
			["SAL-0001", "TIMETREX-YTD-2026-HR-EMP-00001"],
			[1000.0, 250.25],
		]

		result = prior_taxable_wages(
			get_all=get_all,
			employee="HR-EMP-00001",
			current_slip="SAL-0002",
			posting_date="2026-09-01",
			taxable_components={"Basic", "Tips"},
		)

		self.assertEqual(result, Decimal("1250.25"))
		self.assertEqual(get_all.call_args_list[2].args, ("Salary Detail",))
		self.assertEqual(get_all.call_args_list[2].kwargs["filters"]["parentfield"], "earnings")

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
		self.assertEqual(get_all.call_count, 2)

	def test_rejects_another_draft_slip_in_the_tax_year(self) -> None:
		get_all = MagicMock(return_value=["SAL-DRAFT-0001"])

		with self.assertRaisesRegex(ConflictingDraftSalarySlipsError, "SAL-DRAFT-0001"):
			prior_taxable_wages(
				get_all=get_all,
				employee="HR-EMP-00001",
				current_slip="SAL-0002",
				posting_date="2026-09-01",
				taxable_components={"Basic"},
			)

	def test_opening_wages_cross_supported_thresholds_without_a_virtual_slip(self) -> None:
		def opening_wages(amount: str) -> Decimal:
			return prior_taxable_wages(
				get_all=MagicMock(return_value=[]),
				employee="HR-EMP-00001",
				current_slip="SAL-0001",
				posting_date="2026-09-01",
				taxable_components={"Basic"},
				opening_taxable_wages=Decimal(amount),
			)

		self.assertEqual(
			calculate_social_security_withholding(
				taxable_wages=Decimal("1000.00"),
				prior_taxable_wages=opening_wages("184000.00"),
				tax_year=2026,
			),
			Decimal("31.00"),
		)
		self.assertEqual(
			calculate_futa_liability(
				taxable_wages=Decimal("1000.00"),
				prior_taxable_wages=opening_wages("6500.00"),
				tax_year=2026,
			),
			Decimal("3.00"),
		)
		medicare = calculate_medicare_liability(
			taxable_wages=Decimal("2000.00"),
			prior_taxable_wages=opening_wages("199000.00"),
		)
		self.assertEqual(medicare.standard_employee, Decimal("29.00"))
		self.assertEqual(medicare.additional_employee, Decimal("9.00"))
		self.assertEqual(medicare.total_employee, Decimal("38.00"))


if __name__ == "__main__":
	unittest.main()
