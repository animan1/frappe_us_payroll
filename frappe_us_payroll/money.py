from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def round_money(value: Decimal) -> Decimal:
	"""Round a monetary amount to cents using conventional half-up rounding."""
	return value.quantize(CENT, rounding=ROUND_HALF_UP)


def wages_below_base(
	current_wages: Decimal,
	prior_wages: Decimal,
	wage_base: Decimal,
) -> Decimal:
	"""Return current-period wages remaining under an annual wage base."""
	return min(current_wages, max(wage_base - prior_wages, ZERO))
