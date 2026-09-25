from decimal import Decimal

from frappe_us_payroll.money import ZERO


def wages_below_base(
	current_wages: Decimal,
	prior_wages: Decimal,
	wage_base: Decimal,
) -> Decimal:
	"""Return current-period wages remaining under an annual wage base."""
	return min(current_wages, max(wage_base - prior_wages, ZERO))
