from datetime import date, datetime


def as_date(value: date | datetime | str) -> date:
	"""Normalize the date representations returned by Frappe documents."""
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(value)
