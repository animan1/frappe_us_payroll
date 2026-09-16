import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields

from frappe_us_payroll.custom_fields import get_custom_fields
from frappe_us_payroll.payroll.income_tax import FEDERAL_INCOME_TAX_COMPONENT
from frappe_us_payroll.payroll.social_security import (
	SOCIAL_SECURITY_COMPONENT,
	SOCIAL_SECURITY_COMPONENT_ABBR,
)

TAXABLE_EARNING_FIELDS = (
	"us_social_security_taxable",
	"us_federal_income_taxable",
)
SALARY_COMPONENTS = {
	SOCIAL_SECURITY_COMPONENT: {
		"salary_component_abbr": SOCIAL_SECURITY_COMPONENT_ABBR,
		"description": "Employee Social Security tax withheld by Frappe US Payroll",
	},
	FEDERAL_INCOME_TAX_COMPONENT: {
		"salary_component_abbr": "FIT",
		"description": "Federal income tax withheld by Frappe US Payroll",
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
		# Existing components may have live abbreviations, formulas, or account mappings.
		if frappe.db.exists("Salary Component", component_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Salary Component",
				"salary_component": component_name,
				"type": "Deduction",
				"depends_on_payment_days": 0,
				"remove_if_zero_valued": 0,
				**values,
			}
		).insert(ignore_permissions=True)


def enable_taxability_for_existing_earnings(fieldname: str) -> None:
	"""Apply a new taxability field's default-on policy to existing earnings."""
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
