UI_SMOKE_TEST_AMOUNT = 12.34
UI_SMOKE_TEST_COMPONENT = "US Payroll Integration Test"
UI_SMOKE_TEST_CONFIG_KEY = "enable_us_payroll_ui_smoke_test"


def apply_us_payroll_deductions(salary_slip) -> None:
	"""Apply US deductions before HRMS finalizes Salary Slip totals.

	The only current behavior is an explicitly enabled development-site smoke
	test. Ordinary sites remain inert until the first federal calculator is added.
	"""
	import frappe

	if frappe.conf.get(UI_SMOKE_TEST_CONFIG_KEY):
		set_deduction_amount(salary_slip, UI_SMOKE_TEST_COMPONENT, UI_SMOKE_TEST_AMOUNT)


def set_deduction_amount(salary_slip, component_name: str, amount) -> bool:
	"""Set an existing deduction row and report whether it was found."""
	for deduction in salary_slip.get("deductions") or ():
		if deduction.salary_component == component_name:
			deduction.amount = amount
			deduction.default_amount = amount
			return True

	return False
