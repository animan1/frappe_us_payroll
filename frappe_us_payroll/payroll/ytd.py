from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal

GetAll = Callable[..., list[object]]


def prior_taxable_wages(
	*,
	get_all: GetAll,
	employee: str,
	current_slip: str,
	posting_date: date | datetime | str,
	taxable_components: set[str],
) -> Decimal:
	"""Sum matching earning rows from the employee's submitted slips this year."""
	if not taxable_components:
		return Decimal("0.00")
	through_date = _date(posting_date)
	salary_slips = get_all(
		"Salary Slip",
		filters={
			"employee": employee,
			"docstatus": 1,
			"name": ("!=", current_slip),
			"posting_date": ("between", (through_date.replace(month=1, day=1), through_date)),
		},
		pluck="name",
	)
	if not salary_slips:
		return Decimal("0.00")
	values = get_all(
		"Salary Detail",
		filters={
			"parent": ("in", tuple(salary_slips)),
			"parenttype": "Salary Slip",
			"parentfield": "earnings",
			"salary_component": ("in", tuple(sorted(taxable_components))),
		},
		pluck="amount",
	)
	return sum((Decimal(str(value or 0)) for value in values), Decimal("0.00"))


def _date(value: date | datetime | str) -> date:
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(value)
