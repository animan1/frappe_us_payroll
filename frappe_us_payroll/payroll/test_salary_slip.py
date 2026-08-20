from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip

from frappe_us_payroll.payroll.salary_slip import set_deduction_amount

TEST_AMOUNT = 12.34
TEST_COMPONENT = "US Payroll Smoke Test"


class SalarySlipRegionalOverrideTest(UnitTestCase):
	def test_smoke_deduction_is_applied_before_net_pay_totals(self):
		previous_country = frappe.flags.country
		previous_company = frappe.flags.company
		frappe.flags.country = "United States"
		frappe.flags.company = None

		def inject_test_deduction(salary_slip):
			set_deduction_amount(salary_slip, TEST_COMPONENT, TEST_AMOUNT)

		try:
			with patch(
				"frappe_us_payroll.payroll.salary_slip.apply_us_payroll_deductions",
				side_effect=inject_test_deduction,
			):
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
					{"salary_component": TEST_COMPONENT, "amount": 0},
				)
				salary_slip.gross_pay = 17.13

				salary_slip.apply_regional_deductions()
				salary_slip.set_net_pay()

				self.assertEqual(salary_slip.deductions[0].amount, TEST_AMOUNT)
				self.assertEqual(salary_slip.total_deduction, TEST_AMOUNT)
				self.assertAlmostEqual(salary_slip.net_pay, 4.79, places=2)
		finally:
			frappe.flags.country = previous_country
			frappe.flags.company = previous_company
