from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def round_money(value: Decimal) -> Decimal:
	"""Round a monetary amount to cents using conventional half-up rounding."""
	return value.quantize(CENT, rounding=ROUND_HALF_UP)
