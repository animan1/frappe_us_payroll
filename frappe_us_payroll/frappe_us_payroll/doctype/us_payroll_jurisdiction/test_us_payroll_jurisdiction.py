from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from frappe_us_payroll.custom_fields import WASHINGTON


class TestUSPayrollJurisdiction(IntegrationTestCase):
	def test_saving_payroll_settings_installs_selected_jurisdiction(self) -> None:
		settings = frappe.get_single("Payroll Settings")
		settings.set("us_payroll_jurisdictions", [])
		settings.append("us_payroll_jurisdictions", {"jurisdiction": WASHINGTON})

		with (
			patch("frappe_us_payroll.setup.create_custom_fields") as create_custom_fields,
			patch("frappe_us_payroll.setup.enable_taxability_for_existing_earnings"),
			patch("frappe_us_payroll.setup.install_salary_components") as install_components,
		):
			settings.save()

		jurisdiction_fields = create_custom_fields.call_args_list[-1].args[0]
		self.assertIn(
			"wa_cares_exempt",
			[field["fieldname"] for field in jurisdiction_fields["Employee"]],
		)
		install_components.assert_called_once_with({WASHINGTON})
