from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal

GetAll = Callable[..., list[object]]


class ConflictingDraftSalarySlipsError(ValueError):
	pass


def prior_taxable_wages(
	*,
	get_all: GetAll,
	employee: str,
	current_slip: str,
	posting_date: date | datetime | str,
	taxable_components: set[str],
	opening_taxable_wages: Decimal = Decimal("0.00"),
) -> Decimal:
	"""Combine opening wages with matching rows from submitted slips this year."""
	through_date = _date(posting_date)
	draft_slips = get_all(
		"Salary Slip",
		filters={
			"employee": employee,
			"docstatus": 0,
			"name": ("!=", current_slip),
			"posting_date": (
				"between",
				(through_date.replace(month=1, day=1), through_date.replace(month=12, day=31)),
			),
		},
		pluck="name",
	)
	if draft_slips:
		raise ConflictingDraftSalarySlipsError(
			"Submit or cancel the employee's other draft Salary Slips before calculating this one: "
			+ ", ".join(str(name) for name in draft_slips)
		)
	if not taxable_components:
		return opening_taxable_wages
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
		return opening_taxable_wages
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
	return opening_taxable_wages + sum(
		(Decimal(str(value or 0)) for value in values),
		Decimal("0.00"),
	)


def _date(value: date | datetime | str) -> date:
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(value)
