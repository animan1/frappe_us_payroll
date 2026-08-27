from typing import TypeAlias

CustomFieldValue: TypeAlias = str | int
CustomFieldDefinition: TypeAlias = dict[str, CustomFieldValue]
CustomFieldMap: TypeAlias = dict[str, list[CustomFieldDefinition]]
FILING_STATUS = {
	"": "",
	"Single or Married filing separately": "single",
	"Married filing jointly or Qualifying surviving spouse": "married",
	"Head of household": "hoh",
}


def get_custom_fields() -> CustomFieldMap:
	"""Return the persisted inputs and outputs needed for Social Security wages."""
	return {
		"Employee": [
			{
				"fieldname": "us_w4_section",
				"label": "US Federal Withholding",
				"fieldtype": "Section Break",
				"insert_after": "payroll_cost_center",
			},
			{
				"fieldname": "us_w4_filing_status",
				"label": "W-4 Filing Status",
				"fieldtype": "Select",
				"options": "\n".join(FILING_STATUS.keys()),
				"insert_after": "us_w4_section",
			},
			{
				"fieldname": "us_w4_step_2",
				"label": "Step 2: Multiple Jobs / Spouse Works",
				"fieldtype": "Check",
				"insert_after": "us_w4_filing_status",
			},
			{
				"fieldname": "us_w4_dependents_amount",
				"label": "Step 3: Dependents and Other Credits",
				"fieldtype": "Currency",
				"default": "0",
				"insert_after": "us_w4_step_2",
			},
			{
				"fieldname": "us_w4_other_income",
				"label": "Step 4(a): Other Income",
				"fieldtype": "Currency",
				"default": "0",
				"insert_after": "us_w4_dependents_amount",
			},
			{
				"fieldname": "us_w4_deductions",
				"label": "Step 4(b): Deductions",
				"fieldtype": "Currency",
				"default": "0",
				"insert_after": "us_w4_other_income",
			},
			{
				"fieldname": "us_w4_extra_withholding",
				"label": "Step 4(c): Extra Withholding",
				"fieldtype": "Currency",
				"default": "0",
				"insert_after": "us_w4_deductions",
			},
		],
		"Salary Component": [
			{
				"fieldname": "us_social_security_taxable",
				"label": "Subject to US Social Security",
				"fieldtype": "Check",
				"insert_after": "description",
				"depends_on": 'eval:doc.type == "Earning"',
				"description": (
					"Leave checked for wages. Uncheck only when this earning is excluded "
					"from Social Security wages."
				),
				"default": "1",
			},
		],
		"Salary Structure Assignment": [
			{
				"fieldname": "us_payroll_opening_balances_section",
				"label": "US Payroll Opening Balances",
				"fieldtype": "Section Break",
				"insert_after": "leave_encashment_amount_per_day",
			},
			{
				"fieldname": "us_social_security_taxable_wages_till_date",
				"label": "US Social Security Taxable Wages Till Date",
				"fieldtype": "Currency",
				"insert_after": "us_payroll_opening_balances_section",
				"description": "Opening year-to-date wages before payroll begins in Frappe",
				"options": "currency",
				"non_negative": 1,
				"allow_on_submit": 1,
			},
			{
				"fieldname": "futa_calculated",
				"label": "FUTA Calculated",
				"fieldtype": "Currency",
				"insert_after": "us_social_security_taxable_wages_till_date",
				"description": "",
				"options": "currency",
				"read_only": 1,
				"no_copy": 1,
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
			{
				"fieldname": "futa_calculated",
				"label": "FUTA Calculated",
				"fieldtype": "Currency",
				"insert_after": "employer_contributions",
				"description": "",
				"options": "currency",
				"read_only": 1,
				"no_copy": 1,
			},
		],
	}
