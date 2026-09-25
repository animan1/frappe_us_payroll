from collections.abc import Collection
from typing import TypeAlias

CustomFieldValue: TypeAlias = str | int
CustomFieldDefinition: TypeAlias = dict[str, CustomFieldValue]
CustomFieldMap: TypeAlias = dict[str, list[CustomFieldDefinition]]
W4_FILING_STATUSES = {
	"Single or Married filing separately": "single",
	"Married filing jointly or Qualifying surviving spouse": "married",
	"Head of household": "hoh",
}
WASHINGTON = "Washington"
JURISDICTION_FIELD_PREFIXES = {WASHINGTON: ("wa_",)}
SUPPORTED_JURISDICTIONS = frozenset(JURISDICTION_FIELD_PREFIXES)


def get_custom_fields(jurisdictions: Collection[str] = ()) -> CustomFieldMap:
	"""Return app-owned payroll inputs and calculated wage fields."""
	fields: CustomFieldMap = {
		"Payroll Settings": [
			{
				"fieldname": "us_payroll_jurisdictions",
				"label": "US Payroll Jurisdictions",
				"fieldtype": "Table",
				"options": "US Payroll Jurisdiction",
				"insert_after": "create_overtime_slip",
				"description": "Select each state where this site calculates payroll.",
			},
		],
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
				"options": "\n" + "\n".join(W4_FILING_STATUSES),
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
			{
				"fieldname": "wa_payroll_section",
				"label": "Washington Payroll",
				"fieldtype": "Section Break",
				"insert_after": "us_w4_extra_withholding",
			},
			{
				"fieldname": "wa_paid_leave_exempt",
				"label": "Exempt from WA Paid Leave",
				"fieldtype": "Check",
				"default": "0",
				"insert_after": "wa_payroll_section",
			},
			{
				"fieldname": "wa_cares_exempt",
				"label": "Exempt from WA Cares",
				"fieldtype": "Check",
				"default": "0",
				"insert_after": "wa_paid_leave_exempt",
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
			{
				"fieldname": "us_federal_income_taxable",
				"label": "Subject to US Federal Income Tax Withholding",
				"fieldtype": "Check",
				"insert_after": "us_social_security_taxable",
				"depends_on": 'eval:doc.type == "Earning"',
				"description": (
					"Leave checked for wages. Uncheck only when this earning is excluded "
					"from federal income tax withholding wages."
				),
				"default": "1",
			},
			{
				"fieldname": "us_medicare_taxable",
				"label": "Subject to US Medicare",
				"fieldtype": "Check",
				"insert_after": "us_federal_income_taxable",
				"depends_on": 'eval:doc.type == "Earning"',
				"description": (
					"Leave checked for ordinary wages. Uncheck only for a payment excluded "
					"from Medicare wages, such as a qualifying nontaxable fringe benefit."
				),
				"default": "1",
			},
			{
				"fieldname": "us_futa_taxable",
				"label": "Subject to FUTA",
				"fieldtype": "Check",
				"insert_after": "us_medicare_taxable",
				"depends_on": 'eval:doc.type == "Earning"',
				"description": (
					"Leave checked for ordinary wages. Uncheck only for a payment excluded "
					"from FUTA wages; employee- or employer-level FUTA exemptions require "
					"separate applicability rules."
				),
				"default": "1",
			},
			{
				"fieldname": "wa_paid_leave_taxable",
				"label": "Subject to WA Paid Leave and WA Cares",
				"fieldtype": "Check",
				"insert_after": "us_futa_taxable",
				"depends_on": 'eval:doc.type == "Earning"',
				"description": "Uncheck for tips and other earnings excluded from Washington wages.",
				"default": "1",
			},
			{
				"fieldname": "wa_unemployment_taxable",
				"label": "Subject to WA Unemployment",
				"fieldtype": "Check",
				"insert_after": "wa_paid_leave_taxable",
				"depends_on": 'eval:doc.type == "Earning"',
				"description": "Uncheck only when this earning is excluded from WA unemployment wages.",
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
				"fieldname": "us_medicare_taxable_wages_till_date",
				"label": "US Medicare Taxable Wages Till Date",
				"fieldtype": "Currency",
				"insert_after": "us_social_security_taxable_wages_till_date",
				"description": "Opening year-to-date wages before payroll begins in Frappe",
				"options": "currency",
				"non_negative": 1,
				"allow_on_submit": 1,
			},
			{
				"fieldname": "us_futa_taxable_wages_till_date",
				"label": "US FUTA Taxable Wages Till Date",
				"fieldtype": "Currency",
				"insert_after": "us_medicare_taxable_wages_till_date",
				"description": "Opening year-to-date wages before payroll begins in Frappe",
				"options": "currency",
				"non_negative": 1,
				"allow_on_submit": 1,
			},
			{
				"fieldname": "wa_payroll_configuration_section",
				"label": "Washington Payroll",
				"fieldtype": "Section Break",
				"insert_after": "us_futa_taxable_wages_till_date",
			},
			{
				"fieldname": "wa_payroll_enabled",
				"label": "Calculate Washington Payroll",
				"fieldtype": "Check",
				"default": "0",
				"insert_after": "wa_payroll_configuration_section",
				"allow_on_submit": 1,
			},
			{
				"fieldname": "wa_pfml_employer_share_required",
				"label": "Pay WA Paid Leave Employer Share",
				"fieldtype": "Check",
				"default": "0",
				"insert_after": "wa_payroll_enabled",
				"allow_on_submit": 1,
			},
			{
				"fieldname": "wa_unemployment_rate",
				"label": "WA Unemployment Rate",
				"fieldtype": "Percent",
				"insert_after": "wa_pfml_employer_share_required",
				"description": "Employer-specific rate from the Employment Security Department.",
				"allow_on_submit": 1,
			},
			{
				"fieldname": "wa_li_employee_rate_per_hour",
				"label": "WA L&I Employee Rate per Hour",
				"fieldtype": "Float",
				"precision": "6",
				"insert_after": "wa_unemployment_rate",
				"allow_on_submit": 1,
			},
			{
				"fieldname": "wa_li_employer_rate_per_hour",
				"label": "WA L&I Employer Rate per Hour",
				"fieldtype": "Float",
				"precision": "6",
				"insert_after": "wa_li_employee_rate_per_hour",
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
			{
				"fieldname": "us_medicare_taxable_wages",
				"label": "US Medicare Taxable Wages",
				"fieldtype": "Currency",
				"insert_after": "us_social_security_taxable_wages",
				"description": "Wages from this slip subject to Medicare",
				"options": "currency",
				"read_only": 1,
				"no_copy": 1,
			},
			{
				"fieldname": "us_futa_taxable_wages",
				"label": "US FUTA Taxable Wages",
				"fieldtype": "Currency",
				"insert_after": "us_medicare_taxable_wages",
				"description": "Wages from this slip subject to FUTA before its annual wage limit",
				"options": "currency",
				"read_only": 1,
				"no_copy": 1,
				"print_hide": 1,
			},
			{
				"fieldname": "wa_paid_leave_taxable_wages",
				"label": "WA Paid Leave Taxable Wages",
				"fieldtype": "Currency",
				"insert_after": "us_futa_taxable_wages",
				"options": "currency",
				"read_only": 1,
				"no_copy": 1,
			},
			{
				"fieldname": "wa_unemployment_taxable_wages",
				"label": "WA Unemployment Taxable Wages",
				"fieldtype": "Currency",
				"insert_after": "wa_paid_leave_taxable_wages",
				"options": "currency",
				"read_only": 1,
				"no_copy": 1,
			},
		],
	}
	return {
		doctype: [
			field
			for field in definitions
			if (jurisdiction := _field_jurisdiction(field)) is None or jurisdiction in jurisdictions
		]
		for doctype, definitions in fields.items()
	}


def _field_jurisdiction(field: CustomFieldDefinition) -> str | None:
	fieldname = field["fieldname"]
	if not isinstance(fieldname, str):
		return None
	for jurisdiction, prefixes in JURISDICTION_FIELD_PREFIXES.items():
		if fieldname.startswith(prefixes):
			return jurisdiction
	return None
