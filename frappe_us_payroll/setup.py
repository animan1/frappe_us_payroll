from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields

from frappe_us_payroll.custom_fields import get_custom_fields


def install_custom_fields() -> None:
	"""Create or update the app-owned payroll fields."""
	create_custom_fields(get_custom_fields(), update=True)


def uninstall_custom_fields() -> None:
	"""Remove the app-owned payroll fields during app uninstall."""
	delete_custom_fields(get_custom_fields())
