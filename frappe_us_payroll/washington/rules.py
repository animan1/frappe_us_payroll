from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import TypeVar

CENT = Decimal("0.01")
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
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
	tax_year: int,
	employer_share_required: bool,
) -> PaidLeaveLiability:
	"""Calculate WA Paid Family and Medical Leave premiums for this period."""
	rule = _rule(PAID_LEAVE_RULES, tax_year, "Paid Leave")
	covered_wages = _wages_below_base(taxable_wages, prior_taxable_wages, rule.wage_base)
	employee_rate = rule.total_rate * rule.employee_share
	employer_rate = rule.total_rate - employee_rate
	return PaidLeaveLiability(
		employee=_money(covered_wages * employee_rate),
		employer=_money(covered_wages * employer_rate) if employer_share_required else CENT * 0,
	)


def calculate_cares(*, taxable_wages: Decimal, tax_year: int) -> Decimal:
	"""Calculate the employee WA Cares premium, which has no annual wage cap."""
	rate = _rule(CARES_RATES, tax_year, "WA Cares")
	return _money(taxable_wages * rate)


def calculate_unemployment(
	*,
	taxable_wages: Decimal,
	prior_taxable_wages: Decimal,
	tax_year: int,
	employer_rate: Decimal,
) -> Decimal:
	"""Calculate employer WA unemployment using the employer's assigned rate."""
	wage_base = _rule(UNEMPLOYMENT_WAGE_BASES, tax_year, "unemployment")
	covered_wages = _wages_below_base(taxable_wages, prior_taxable_wages, wage_base)
	return _money(covered_wages * employer_rate)


def calculate_industrial_insurance(
	*, hours: Decimal, employee_rate_per_hour: Decimal, employer_rate_per_hour: Decimal
) -> tuple[Decimal, Decimal]:
	"""Calculate employee and employer L&I premiums from assigned hourly rates."""
	return (
		_money(hours * employee_rate_per_hour),
		_money(hours * employer_rate_per_hour),
	)


def _wages_below_base(wages: Decimal, prior_wages: Decimal, wage_base: Decimal) -> Decimal:
	return min(wages, max(wage_base - prior_wages, Decimal("0.00")))


def _money(value: Decimal) -> Decimal:
	return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _rule(rules: dict[int, Rule], tax_year: int, name: str) -> Rule:
	try:
		return rules[tax_year]
	except KeyError as error:
		raise ValueError(f"Washington {name} rules are not available for {tax_year}") from error
