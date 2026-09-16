from datetime import date, datetime


def posting_date(value: date | datetime | str) -> date:
	"""Normalize Frappe's supported posting-date representations."""
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(value)
