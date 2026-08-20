from decimal import Decimal

def withholding(
	*,
	taxable_wages: Decimal,
	taxable_wages_ytd: Decimal = ...,
	self_employed: bool = ...,
	tax_year: int = ...,
	rounded: bool = ...,
) -> Decimal: ...
