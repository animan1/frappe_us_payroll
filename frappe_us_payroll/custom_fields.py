from typing import TypeAlias

CustomFieldValue: TypeAlias = str | int
CustomFieldDefinition: TypeAlias = dict[str, CustomFieldValue]
CustomFieldMap: TypeAlias = dict[str, list[CustomFieldDefinition]]


def get_custom_fields() -> CustomFieldMap:
	"""Return the persisted inputs and outputs needed for Social Security wages."""
	return {
		"Salary Component": [
			{
				"fieldname": "us_social_security_taxable",
				"label": "Subject to US Social Security",
				"fieldtype": "Check",
				"insert_after": "description",
				"depends_on": 'eval:doc.type == "Earning"',
				"default": 0,
			},
		],
		"Salary Structure Assignment": [
			{
				"fieldname": "us_social_security_taxable_wages_till_date",
				"label": "US Social Security Taxable Wages Till Date",
				"fieldtype": "Currency",
				"insert_after": "taxable_earnings_till_date",
				"description": "Opening year-to-date wages before payroll begins in Frappe",
				"options": "currency",
				"non_negative": 1,
				"allow_on_submit": 1,
			},
		],
		"Salary Slip": [
			{
				"fieldname": "us_social_security_taxable_wages",
				"label": "US Social Security Taxable Wages",
				"fieldtype": "Currency",
				"insert_after": "gross_pay",
				"description": "Wages from this slip subject to US Social Security",
				"options": "currency",
				"read_only": 1,
				"no_copy": 1,
			},
		],
	}
