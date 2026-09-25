"""Washington payroll calculations using published 2026 agency rules.

Sources:
- https://paidleave.wa.gov/updates/
- https://wacaresfund.wa.gov/help-support/frequently-asked-questions
- https://esd.wa.gov/employer-requirements/unemployment-taxes/how-we-determine-tax-rates
- https://www.lni.wa.gov/insurance/rates-risk-classes/rates-for-workers-compensation/calculating-premium-rates
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import TypeVar

from frappe_us_payroll.money import ZERO, round_money
from frappe_us_payroll.wage_base import wages_below_base

Rule = TypeVar("Rule")


@dataclass(frozen=True)
class PaidLeaveRule:
	wage_base: Decimal
	total_rate: Decimal
	employee_share: Decimal


@dataclass(frozen=True)
class PaidLeaveLiability:
	employee: Decimal
	employer: Decimal


PAID_LEAVE_RULES = {
	2026: PaidLeaveRule(
		wage_base=Decimal("184500.00"),
		total_rate=Decimal("0.0113"),
		employee_share=Decimal("0.7143"),
	),
}
CARES_RATES = {2026: Decimal("0.0058")}
UNEMPLOYMENT_WAGE_BASES = {2026: Decimal("78200.00")}


def calculate_paid_leave(
	*,
	covered_wages: Decimal,
	prior_covered_wages: Decimal,
	tax_year: int,
	employer_share_required: bool,
) -> PaidLeaveLiability:
	"""Calculate Paid Leave on covered wages; callers must exclude tips."""
	rule = _rule(PAID_LEAVE_RULES, tax_year, "Paid Leave")
	wages_subject_to_premium = wages_below_base(covered_wages, prior_covered_wages, rule.wage_base)
	employee_rate = rule.total_rate * rule.employee_share
	employer_rate = rule.total_rate - employee_rate
	return PaidLeaveLiability(
		employee=round_money(wages_subject_to_premium * employee_rate),
		employer=round_money(wages_subject_to_premium * employer_rate) if employer_share_required else ZERO,
	)


def calculate_cares(*, covered_wages: Decimal, tax_year: int) -> Decimal:
	"""Calculate WA Cares on covered wages, excluding tips and without a wage cap."""
	rate = _rule(CARES_RATES, tax_year, "WA Cares")
	return round_money(covered_wages * rate)


def calculate_unemployment(
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
	tax_year: int,
	employer_rate: Decimal,
) -> Decimal:
	"""Calculate employer WA unemployment using the employer's assigned rate."""
	wage_base = _rule(UNEMPLOYMENT_WAGE_BASES, tax_year, "unemployment")
	covered_wages = wages_below_base(taxable_wages, prior_taxable_wages, wage_base)
	return round_money(covered_wages * employer_rate)


def calculate_industrial_insurance(
	*, hours: Decimal, employee_rate_per_hour: Decimal, employer_rate_per_hour: Decimal
) -> tuple[Decimal, Decimal]:
	"""Calculate employee and employer L&I premiums from assigned hourly rates."""
	return (
		round_money(hours * employee_rate_per_hour),
		round_money(hours * employer_rate_per_hour),
	)


def _rule(rules: dict[int, Rule], tax_year: int, name: str) -> Rule:
	try:
		return rules[tax_year]
	except KeyError as error:
		raise ValueError(f"Washington {name} rules are not available for {tax_year}") from error
