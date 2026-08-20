import unittest
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from frappe_us_payroll.payroll.components import DeductionRow
from frappe_us_payroll.payroll.social_security import (
	SOCIAL_SECURITY_COMPONENT,
	EarningRow,
	apply_social_security_withholding,
	taxable_wages,
)


@dataclass
class FakeEarning:
	salary_component: str
	amount: float


@dataclass
class FakeDeduction:
	salary_component: str
	amount: float = 0
	default_amount: float = 0


class FakeSalarySlip:
	posting_date: date | datetime | str = date(2026, 8, 20)
	us_social_security_taxable_wages: float = 0.0

	def __init__(self, earnings: list[FakeEarning]) -> None:
		self.earnings: Iterable[EarningRow] = earnings
		self.deductions = [FakeDeduction(SOCIAL_SECURITY_COMPONENT)]

	def get(self, fieldname: str) -> Iterable[DeductionRow] | None:
		return self.deductions if fieldname == "deductions" else None


class SocialSecurityPayrollTest(unittest.TestCase):
	def test_sums_only_subject_earnings(self) -> None:
		earnings = [FakeEarning("Basic", 1000), FakeEarning("Expense Reimbursement", 50)]

		self.assertEqual(taxable_wages(earnings, {"Basic"}), Decimal("1000"))

	def test_maps_current_wages_and_withholding_to_salary_slip(self) -> None:
		slip = FakeSalarySlip([FakeEarning("Basic", 1000), FakeEarning("Expense Reimbursement", 50)])

		withholding = apply_social_security_withholding(
			slip,
			taxable_components={"Basic"},
			prior_taxable_wages=Decimal("0"),
			opening_taxable_wages=Decimal("0"),
		)

		self.assertEqual(withholding, Decimal("62.00"))
		self.assertEqual(slip.us_social_security_taxable_wages, 1000)
		self.assertEqual(slip.deductions[0].amount, 62)

	def test_opening_and_submitted_wages_apply_the_annual_wage_base(self) -> None:
		slip = FakeSalarySlip([FakeEarning("Basic", 1000)])

		withholding = apply_social_security_withholding(
			slip,
			taxable_components={"Basic"},
			prior_taxable_wages=Decimal("183000"),
			opening_taxable_wages=Decimal("1000"),
		)

		self.assertEqual(withholding, Decimal("31.00"))


if __name__ == "__main__":
	unittest.main()
