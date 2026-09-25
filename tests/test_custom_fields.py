import unittest

from frappe_us_payroll.custom_fields import WASHINGTON, get_custom_fields


class CustomFieldsTest(unittest.TestCase):
	def test_defines_payroll_fields_on_each_source_document(self) -> None:
		custom_fields = get_custom_fields({WASHINGTON})

		self.assertEqual(
			{doctype: [field["fieldname"] for field in fields] for doctype, fields in custom_fields.items()},
			{
				"Payroll Settings": ["us_payroll_jurisdictions"],
				"Employee": [
					"us_w4_section",
					"us_w4_filing_status",
					"us_w4_step_2",
					"us_w4_dependents_amount",
					"us_w4_other_income",
					"us_w4_deductions",
					"us_w4_extra_withholding",
					"wa_payroll_section",
					"wa_paid_leave_exempt",
					"wa_cares_exempt",
				],
				"Salary Component": [
					"us_social_security_taxable",
					"us_federal_income_taxable",
					"us_medicare_taxable",
					"us_futa_taxable",
					"wa_paid_leave_taxable",
					"wa_unemployment_taxable",
				],
				"Salary Structure Assignment": [
					"us_payroll_opening_balances_section",
					"us_social_security_taxable_wages_till_date",
					"us_medicare_taxable_wages_till_date",
					"us_futa_taxable_wages_till_date",
					"wa_payroll_configuration_section",
					"wa_payroll_enabled",
					"wa_pfml_employer_share_required",
					"wa_unemployment_rate",
					"wa_li_employee_rate_per_hour",
					"wa_li_employer_rate_per_hour",
				],
				"Salary Slip": [
					"us_social_security_taxable_wages",
					"us_medicare_taxable_wages",
					"us_futa_taxable_wages",
					"wa_paid_leave_taxable_wages",
					"wa_unemployment_taxable_wages",
				],
			},
		)

	def test_opening_wages_remain_editable_after_assignment_submission(self) -> None:
		fields = {field["fieldname"]: field for field in get_custom_fields()["Salary Structure Assignment"]}
		section_field = fields["us_payroll_opening_balances_section"]
		assignment_fields = [
			fields["us_social_security_taxable_wages_till_date"],
			fields["us_medicare_taxable_wages_till_date"],
			fields["us_futa_taxable_wages_till_date"],
		]

		self.assertEqual(section_field["fieldtype"], "Section Break")
		self.assertEqual(assignment_fields[0]["insert_after"], section_field["fieldname"])
		self.assertTrue(all(field["allow_on_submit"] == 1 for field in assignment_fields))
		self.assertTrue(all(field["non_negative"] == 1 for field in assignment_fields))

	def test_earning_taxability_defaults_on(self) -> None:
		for component_field in get_custom_fields({WASHINGTON})["Salary Component"]:
			description = component_field["description"]

			self.assertEqual(component_field["default"], "1")
			if not isinstance(description, str):
				raise AssertionError("Salary Component field description must be text")
			self.assertIn("Uncheck", description)

	def test_salary_slip_wages_are_persisted_output(self) -> None:
		salary_slip_fields = get_custom_fields({WASHINGTON})["Salary Slip"]
		salary_slip_field = salary_slip_fields[0]

		self.assertEqual(salary_slip_field["read_only"], 1)
		self.assertEqual(salary_slip_field["no_copy"], 1)
		self.assertTrue(all(field["read_only"] == 1 for field in salary_slip_fields))
		self.assertTrue(all(field["no_copy"] == 1 for field in salary_slip_fields))

	def test_washington_fields_require_jurisdiction_selection(self) -> None:
		custom_fields = get_custom_fields()

		self.assertEqual(
			["us_payroll_jurisdictions"],
			[field["fieldname"] for field in custom_fields["Payroll Settings"]],
		)
		self.assertFalse(
			any(
				isinstance(field["fieldname"], str) and field["fieldname"].startswith("wa_")
				for definitions in custom_fields.values()
				for field in definitions
			)
		)


if __name__ == "__main__":
	unittest.main()
