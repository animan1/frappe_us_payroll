import frappe
from frappe.tests import IntegrationTestCase

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

from frappe_us_payroll.payroll.social_security import SOCIAL_SECURITY_COMPONENT


class TestSocialSecuritySalarySlip(IntegrationTestCase):
	def test_real_salary_slip_calculates_social_security(self) -> None:
		previous_country = frappe.flags.country
		previous_include_holidays = frappe.db.get_single_value(
			"Payroll Settings", "include_holidays_in_total_working_days"
		)
		frappe.flags.country = "United States"
		frappe.db.set_single_value("Payroll Settings", "include_holidays_in_total_working_days", 1)
		try:
			company = "_Test Company"
			currency = frappe.db.get_value("Company", company, "default_currency")
			holiday_list = frappe.get_doc(
				{
					"doctype": "Holiday List",
					"holiday_list_name": "_Test US Payroll SS 2026",
					"from_date": "2026-01-01",
					"to_date": "2026-12-31",
				}
			).insert()
			holiday_assignment = frappe.get_doc(
				{
					"doctype": "Holiday List Assignment",
					"applicable_for": "Company",
					"assigned_to": company,
					"holiday_list": holiday_list.name,
					"from_date": "2026-01-01",
				}
			).insert()
			holiday_assignment.submit()
			employee = frappe.get_doc(
				{
					"doctype": "Employee",
					"first_name": "US Payroll E2E",
					"company": company,
					"gender": "Female",
					"date_of_birth": "1990-01-01",
					"date_of_joining": "2026-01-01",
					"status": "Active",
				}
			).insert()
			structure = frappe.get_doc(
				{
					"doctype": "Salary Structure",
					"name": "_Test US Payroll SS Salary Structure",
					"company": company,
					"currency": currency,
					"payroll_frequency": "Monthly",
					"is_active": "Yes",
					"earnings": [
						{
							"salary_component": "Basic",
							"abbr": "B",
							"amount": 1000,
							"depends_on_payment_days": 0,
						}
					],
					"deductions": [
						{
							"salary_component": SOCIAL_SECURITY_COMPONENT,
							"abbr": "USSS",
							"amount": 0,
							"depends_on_payment_days": 0,
						}
					],
				}
			).insert()
			structure.submit()
			assignment = frappe.get_doc(
				{
					"doctype": "Salary Structure Assignment",
					"employee": employee.name,
					"salary_structure": structure.name,
					"company": company,
					"currency": currency,
					"from_date": "2026-01-01",
					"base": 1000,
				}
			).insert()
			assignment.submit()

			salary_slip = make_salary_slip(
				structure.name,
				employee=employee.name,
				posting_date="2026-08-20",
			)

			self.assertEqual(salary_slip.gross_pay, 1000)
			self.assertEqual(salary_slip.us_social_security_taxable_wages, 1000)
			self.assertEqual(salary_slip.deductions[0].amount, 62)
			self.assertEqual(salary_slip.total_deduction, 62)
			self.assertEqual(salary_slip.net_pay, 938)
		finally:
			frappe.flags.country = previous_country
			frappe.db.set_single_value(
				"Payroll Settings",
				"include_holidays_in_total_working_days",
				previous_include_holidays,
			)
