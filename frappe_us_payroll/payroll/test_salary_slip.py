import frappe
from frappe.tests import UnitTestCase

from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

from frappe_us_payroll.payroll.salary_slip import (
	UI_SMOKE_TEST_AMOUNT,
	UI_SMOKE_TEST_COMPONENT,
	UI_SMOKE_TEST_CONFIG_KEY,
)


class SalarySlipRegionalOverrideTest(UnitTestCase):
	def test_ui_smoke_mode_is_inert_when_disabled(self) -> None:
		previous_country = frappe.flags.country
		previous_company = frappe.flags.company
		previous_smoke_setting = frappe.conf.get(UI_SMOKE_TEST_CONFIG_KEY)
		frappe.flags.country = "United States"
		frappe.flags.company = None
		frappe.conf[UI_SMOKE_TEST_CONFIG_KEY] = False

		try:
			salary_slip = SalarySlip({"doctype": "Salary Slip"})
			salary_slip.append(
				"deductions",
				{"salary_component": UI_SMOKE_TEST_COMPONENT, "amount": 0},
			)

			salary_slip.apply_regional_deductions()

			self.assertEqual(salary_slip.deductions[0].amount, 0)
		finally:
			frappe.flags.country = previous_country
			frappe.flags.company = previous_company
			if previous_smoke_setting is None:
				frappe.conf.pop(UI_SMOKE_TEST_CONFIG_KEY, None)
			else:
				frappe.conf[UI_SMOKE_TEST_CONFIG_KEY] = previous_smoke_setting

	def test_smoke_deduction_is_applied_before_net_pay_totals(self) -> None:
		previous_country = frappe.flags.country
		previous_company = frappe.flags.company
		previous_smoke_setting = frappe.conf.get(UI_SMOKE_TEST_CONFIG_KEY)
		frappe.flags.country = "United States"
		frappe.flags.company = None
		frappe.conf[UI_SMOKE_TEST_CONFIG_KEY] = True

		try:
			salary_slip = SalarySlip(
				{
					"doctype": "Salary Slip",
					"currency": "USD",
					"exchange_rate": 1,
				}
			)
			salary_slip.append(
				"earnings",
				{"salary_component": "Smoke Test Earnings", "amount": 17.13},
			)
			salary_slip.append(
				"deductions",
				{"salary_component": UI_SMOKE_TEST_COMPONENT, "amount": 0},
			)
			salary_slip.gross_pay = 17.13

			salary_slip.apply_regional_deductions()
			salary_slip.set_net_pay()

			self.assertEqual(salary_slip.deductions[0].amount, UI_SMOKE_TEST_AMOUNT)
			self.assertEqual(salary_slip.total_deduction, UI_SMOKE_TEST_AMOUNT)
			self.assertAlmostEqual(salary_slip.net_pay, 4.79, places=2)
		finally:
			frappe.flags.country = previous_country
			frappe.flags.company = previous_company
			if previous_smoke_setting is None:
				frappe.conf.pop(UI_SMOKE_TEST_CONFIG_KEY, None)
			else:
				frappe.conf[UI_SMOKE_TEST_CONFIG_KEY] = previous_smoke_setting
