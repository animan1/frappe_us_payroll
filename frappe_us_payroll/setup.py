import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields

from frappe_us_payroll.custom_fields import get_custom_fields
from frappe_us_payroll.payroll.component_names import (
	FEDERAL_INCOME_TAX,
	FUTA_EMPLOYER,
	MEDICARE_EMPLOYEE,
	MEDICARE_EMPLOYER,
	SOCIAL_SECURITY_EMPLOYEE,
	SOCIAL_SECURITY_EMPLOYER,
	WA_CARES_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYER,
	WA_PAID_LEAVE_EMPLOYEE,
	WA_PAID_LEAVE_EMPLOYER,
	WA_UNEMPLOYMENT_EMPLOYER,
)

TAXABLE_EARNING_FIELDS = (
	"us_social_security_taxable",
	"us_federal_income_taxable",
	"us_medicare_taxable",
	"us_futa_taxable",
	"wa_paid_leave_taxable",
	"wa_unemployment_taxable",
)
SALARY_COMPONENTS = {
	SOCIAL_SECURITY_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": "FICA_D",
		"description": "Employee Social Security tax withheld by Frappe US Payroll",
	},
	FEDERAL_INCOME_TAX: {
		"type": "Deduction",
		"salary_component_abbr": "FIT",
		"description": "Federal income tax withheld by Frappe US Payroll",
	},
	MEDICARE_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": "Med_D",
		"description": "Employee Medicare tax withheld by Frappe US Payroll",
	},
	SOCIAL_SECURITY_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "FICA_C",
		"description": "Employer Social Security liability calculated by Frappe US Payroll",
	},
	MEDICARE_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "Med_C",
		"description": "Employer Medicare liability calculated by Frappe US Payroll",
	},
	FUTA_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "FUTA",
		"description": "Federal unemployment liability calculated by Frappe US Payroll",
	},
	WA_PAID_LEAVE_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": "WA_PFML_D",
		"description": "Employee WA Paid Leave premium calculated by Frappe US Payroll",
	},
	WA_CARES_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": "WA_Cares",
		"description": "Employee WA Cares premium calculated by Frappe US Payroll",
	},
	WA_INDUSTRIAL_INSURANCE_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": "WA_LI_D",
		"description": "Employee WA L&I premium calculated by Frappe US Payroll",
	},
	WA_PAID_LEAVE_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "WA_PFML_C",
		"description": "Employer WA Paid Leave liability calculated by Frappe US Payroll",
	},
	WA_INDUSTRIAL_INSURANCE_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "WA_LI_C",
		"description": "Employer WA L&I liability calculated by Frappe US Payroll",
	},
	WA_UNEMPLOYMENT_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "WA_UI",
		"description": "Employer WA unemployment liability calculated by Frappe US Payroll",
	},
}


def install_custom_fields() -> None:
	"""Create or update the app-owned payroll fields and components."""
	new_taxability_fields = [
		fieldname
		for fieldname in TAXABLE_EARNING_FIELDS
		if not frappe.db.exists("Custom Field", f"Salary Component-{fieldname}")
	]
	create_custom_fields(get_custom_fields(), update=True)
	for fieldname in new_taxability_fields:
		enable_taxability_for_existing_earnings(fieldname)
	install_salary_components()


def install_salary_components() -> None:
	"""Create required app-owned Salary Components without changing existing configuration."""
	for component_name, values in SALARY_COMPONENTS.items():
		if frappe.db.exists("Salary Component", component_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Salary Component",
				"salary_component": component_name,
				"type": values["type"],
				"depends_on_payment_days": 0,
				"remove_if_zero_valued": 0,
				**values,
			}
		).insert(ignore_permissions=True)


def enable_taxability_for_existing_earnings(fieldname: str) -> None:
	"""Apply a new taxable-by-default field to earning components that predate it."""
	frappe.db.set_value(
		"Salary Component",
		{"type": "Earning"},
		fieldname,
		1,
		update_modified=False,
	)


def enable_social_security_for_existing_earnings() -> None:
	"""Retain the original patch entry point for installed sites."""
	enable_taxability_for_existing_earnings("us_social_security_taxable")


def uninstall_custom_fields() -> None:
	"""Remove the app-owned payroll fields during app uninstall."""
	delete_custom_fields(get_custom_fields())
