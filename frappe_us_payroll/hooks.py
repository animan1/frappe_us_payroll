app_name = "frappe_us_payroll"
app_title = "Frappe US Payroll"
app_publisher = "Frappe US Payroll contributors"
app_description = "US payroll calculations and localization for Frappe HR"
app_email = ""
app_license = "GNU General Public License (v3)"

required_apps = ["frappe/erpnext", "frappe/hrms"]

after_install = "frappe_us_payroll.setup.install_custom_fields"
after_migrate = "frappe_us_payroll.setup.install_custom_fields"
before_uninstall = "frappe_us_payroll.setup.uninstall_custom_fields"

regional_overrides = {
	"United States": {
		"hrms.payroll.doctype.salary_slip.salary_slip.apply_regional_deductions": (
			"frappe_us_payroll.payroll.salary_slip.apply_us_payroll_deductions"
		),
	}
}
