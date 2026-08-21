import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields

from frappe_us_payroll.custom_fields import get_custom_fields
from frappe_us_payroll.payroll.social_security import SOCIAL_SECURITY_COMPONENT
from frappe_us_payroll.payroll.salary_slip import FIT_COMPONENT

SOCIAL_SECURITY_TAXABLE_CUSTOM_FIELD = "Salary Component-us_social_security_taxable"

COMPONENTS = {
	FIT_COMPONENT: {
		"salary_component": FIT_COMPONENT,
		"salary_component_abbr": "FIT",
	},
	SOCIAL_SECURITY_COMPONENT: {
		"salary_component": SOCIAL_SECURITY_COMPONENT,
		"salary_component_abbr": "FICA",
		"description": "Employee Social Security tax withheld by Frappe US Payroll",
	},
}


def install_custom_fields() -> None:
	"""Create or update the app-owned payroll fields and components."""
	initialize_existing_earnings = not frappe.db.exists("Custom Field", SOCIAL_SECURITY_TAXABLE_CUSTOM_FIELD)
	create_custom_fields(get_custom_fields(), update=True)
	if initialize_existing_earnings:
		enable_social_security_for_existing_earnings()
	install_salary_components()


def install_salary_components() -> None:
	"""Create required app-owned Salary Components without changing existing configuration."""
	for component, values in COMPONENTS.items():
		if frappe.db.exists("Salary Component", component):
			continue

		frappe.get_doc(
			{
				"doctype": "Salary Component",
				"type": "Deduction",
				"depends_on_payment_days": 0,
				"remove_if_zero_valued": 0,
				**values,
			}
		).insert(ignore_permissions=True)


def enable_social_security_for_existing_earnings() -> None:
	"""Apply the default-on policy once to earning components that predate the field."""
	frappe.db.set_value(
		"Salary Component",
		{"type": "Earning"},
		"us_social_security_taxable",
		1,
		update_modified=False,
	)


def uninstall_custom_fields() -> None:
	"""Remove the app-owned payroll fields during app uninstall."""
	delete_custom_fields(get_custom_fields())
