import frappe

from frappe_us_payroll.payroll.salary_slip import UI_SMOKE_TEST_COMPONENT


def ensure_ui_smoke_test_component() -> str:
	"""Create the opt-in development component used for manual UI verification."""
	if not frappe.db.exists("Salary Component", UI_SMOKE_TEST_COMPONENT):
		frappe.get_doc(
			{
				"doctype": "Salary Component",
				"salary_component": UI_SMOKE_TEST_COMPONENT,
				"salary_component_abbr": "USPTST",
				"type": "Deduction",
				"depends_on_payment_days": 0,
				"remove_if_zero_valued": 0,
				"description": "Development-only integration check; not a real payroll deduction.",
			}
		).insert(ignore_permissions=True)

	return UI_SMOKE_TEST_COMPONENT
