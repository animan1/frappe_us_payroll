import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields

from frappe_us_payroll.custom_fields import get_custom_fields

SOCIAL_SECURITY_TAXABLE_CUSTOM_FIELD = "Salary Component-us_social_security_taxable"


def install_custom_fields() -> None:
	"""Create or update the app-owned payroll fields."""
	initialize_existing_earnings = not frappe.db.exists("Custom Field", SOCIAL_SECURITY_TAXABLE_CUSTOM_FIELD)
	create_custom_fields(get_custom_fields(), update=True)
	if initialize_existing_earnings:
		enable_social_security_for_existing_earnings()


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
