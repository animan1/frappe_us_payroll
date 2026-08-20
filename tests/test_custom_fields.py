import unittest

from frappe_us_payroll.custom_fields import get_custom_fields


class CustomFieldsTest(unittest.TestCase):
	def test_defines_social_security_fields_on_each_source_document(self) -> None:
		custom_fields = get_custom_fields()

		self.assertEqual(
			{doctype: [field["fieldname"] for field in fields] for doctype, fields in custom_fields.items()},
			{
				"Salary Component": ["us_social_security_taxable"],
				"Salary Structure Assignment": ["us_social_security_taxable_wages_till_date"],
				"Salary Slip": ["us_social_security_taxable_wages"],
			},
		)

	def test_opening_wages_remain_editable_after_assignment_submission(self) -> None:
		assignment_field = get_custom_fields()["Salary Structure Assignment"][0]

		self.assertEqual(assignment_field["allow_on_submit"], 1)
		self.assertEqual(assignment_field["non_negative"], 1)

	def test_social_security_taxability_defaults_on(self) -> None:
		component_field = get_custom_fields()["Salary Component"][0]

		self.assertEqual(component_field["default"], "1")

	def test_salary_slip_wages_are_persisted_output(self) -> None:
		salary_slip_field = get_custom_fields()["Salary Slip"][0]

		self.assertEqual(salary_slip_field["read_only"], 1)
		self.assertEqual(salary_slip_field["no_copy"], 1)


if __name__ == "__main__":
	unittest.main()
