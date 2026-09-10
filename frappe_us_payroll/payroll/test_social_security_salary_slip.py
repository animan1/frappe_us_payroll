import frappe
from frappe.tests import IntegrationTestCase

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

from frappe_us_payroll.payroll.component_names import (
	FEDERAL_INCOME_TAX,
	FUTA_EMPLOYER,
	MEDICARE_EMPLOYEE,
	MEDICARE_EMPLOYER,
	SOCIAL_SECURITY_EMPLOYEE,
	SOCIAL_SECURITY_EMPLOYER,
)


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
			employee = frappe.get_doc(
				{
					"doctype": "Employee",
					"first_name": "US Payroll E2E",
					"company": company,
					"gender": "Female",
					"date_of_birth": "1990-01-01",
					"date_of_joining": "2026-01-01",
					"status": "Active",
					"us_w4_filing_status": "Single or Married filing separately",
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
							"salary_component": SOCIAL_SECURITY_EMPLOYEE,
							"abbr": "FICA_D",
							"amount": 0,
							"depends_on_payment_days": 0,
						},
						{
							"salary_component": FEDERAL_INCOME_TAX,
							"abbr": "FIT",
							"amount": 0,
							"depends_on_payment_days": 0,
						},
						{
							"salary_component": MEDICARE_EMPLOYEE,
							"abbr": "Med_D",
							"amount": 0,
							"depends_on_payment_days": 0,
						},
					],
					"employer_contributions": [
						{
							"salary_component": SOCIAL_SECURITY_EMPLOYER,
							"abbr": "FICA_C",
							"amount": 0,
						},
						{
							"salary_component": MEDICARE_EMPLOYER,
							"abbr": "Med_C",
							"amount": 0,
						},
						{
							"salary_component": FUTA_EMPLOYER,
							"abbr": "FUTA",
							"amount": 0,
						},
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
			deductions = {row.salary_component: row.amount for row in salary_slip.deductions}
			self.assertEqual(deductions[SOCIAL_SECURITY_EMPLOYEE], 62)
			self.assertEqual(deductions[MEDICARE_EMPLOYEE], 14.5)
			contributions = {row.salary_component: row.amount for row in salary_slip.employer_contributions}
			self.assertEqual(contributions[SOCIAL_SECURITY_EMPLOYER], 62)
			self.assertEqual(contributions[MEDICARE_EMPLOYER], 14.5)
			self.assertEqual(contributions[FUTA_EMPLOYER], 6)
			self.assertEqual(salary_slip.total_deduction, 76.5)
			self.assertEqual(salary_slip.net_pay, 923.5)
		finally:
			frappe.flags.country = previous_country
			frappe.db.set_single_value(
				"Payroll Settings",
				"include_holidays_in_total_working_days",
				previous_include_holidays,
			)
