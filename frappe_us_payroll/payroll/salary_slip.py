from decimal import Decimal

import frappe

from frappe_us_payroll.payroll.components import (
	MissingSalaryComponentError,
	SalarySlipDeductions,
	set_deduction_amount,
)

UI_SMOKE_TEST_AMOUNT = Decimal("12.34")
UI_SMOKE_TEST_COMPONENT = "US Payroll Integration Test"
UI_SMOKE_TEST_CONFIG_KEY = "enable_us_payroll_ui_smoke_test"


def apply_us_payroll_deductions(salary_slip: SalarySlipDeductions) -> None:
	"""Apply US deductions before HRMS finalizes Salary Slip totals.

	The only current behavior is an explicitly enabled development-site smoke
	test. Ordinary sites remain inert until the first federal calculator is added.
	"""
	if frappe.conf.get(UI_SMOKE_TEST_CONFIG_KEY):
		try:
			set_deduction_amount(salary_slip, UI_SMOKE_TEST_COMPONENT, UI_SMOKE_TEST_AMOUNT)
		except MissingSalaryComponentError as error:
			frappe.throw(str(error), exc=frappe.ValidationError, title="Missing Salary Component")
