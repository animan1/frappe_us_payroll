import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields

from frappe_us_payroll.custom_fields import get_custom_fields
from frappe_us_payroll.payroll.salary_slip import FIT_COMPONENT
from frappe_us_payroll.payroll.social_security import (
	SOCIAL_SECURITY_EMPLOYEE_COMPONENT,
	SOCIAL_SECURITY_EMPLOYER_COMPONENT,
)

SOCIAL_SECURITY_TAXABLE_CUSTOM_FIELD = "Salary Component-us_social_security_taxable"
FUTA_COMPONENT = "US - Federal Unemployment Insurance"
MEDICARE_EMPLOYEE_COMPONENT = "Medicare - Employee"
MEDICARE_EMPLOYER_COMPONENT = "Medicare - Employer"
LI_EMPLOYEE_COMPONENT = "WA - L&I - Employee (Taproom)"
LI_EMPLOYER_COMPONENT = "WA - L&I - Employer (Taproom)"
WA_CARES_COMPONENT = "WA - WA Cares"
PFML_COMPONENT = "WA - Paid Family and Medical Leave - Employee"
TIPS_PAID_COMPONENT = "Tips Already Paid"


def _salary_component(salary_component, abbr, _type, formula=None, **kwargs):
	comp = {
		"salary_component": salary_component,
		"salary_component_abbr": abbr,
		"type": _type,
		**kwargs,
	}
	if formula:
		comp["amount_based_on_formula"] = 1
		comp["formula"] = formula
	return comp


def _employer_contribution(salary_component, abbr, **kwargs):
	return _salary_component(salary_component, abbr, "Employer Contribution", **kwargs)


def _deduction(salary_component, abbr, **kwargs):
	ded = _salary_component(salary_component, abbr, "Deduction", **kwargs)
	ded["depends_on_payment_days"] = 0
	ded["remove_if_zero_valued"] = 0
	return ded


COMPONENTS = {
	TIPS_PAID_COMPONENT: _deduction(TIPS_PAID_COMPONENT, "TP", formula="T"),
	PFML_COMPONENT: _deduction(PFML_COMPONENT, "PFML", formula="B * .00807159"),
	WA_CARES_COMPONENT: _deduction(WA_CARES_COMPONENT, "WAC", formula="B * .0058"),
	LI_EMPLOYEE_COMPONENT: _deduction(LI_EMPLOYEE_COMPONENT, "LIE", formula="total_working_hours * .1755"),
	MEDICARE_EMPLOYEE_COMPONENT: _deduction(
		MEDICARE_EMPLOYEE_COMPONENT, "Med_D", formula="gross_pay * .0145"
	),
	FIT_COMPONENT: _deduction(FIT_COMPONENT, "FIT"),
	SOCIAL_SECURITY_EMPLOYEE_COMPONENT: _deduction(
		SOCIAL_SECURITY_EMPLOYEE_COMPONENT,
		"FICA_D",
		description="Employee Social Security tax withheld by Frappe US Payroll",
	),
	SOCIAL_SECURITY_EMPLOYER_COMPONENT: _employer_contribution(
		SOCIAL_SECURITY_EMPLOYER_COMPONENT, "FICA_C", formula="FICA_D"
	),
	MEDICARE_EMPLOYER_COMPONENT: _employer_contribution(
		MEDICARE_EMPLOYER_COMPONENT, "Med_C", formula="Med_D"
	),
	FUTA_COMPONENT: _employer_contribution(FUTA_COMPONENT, "FUTA", formula="futa_calculated"),
	LI_EMPLOYER_COMPONENT: _deduction(LI_EMPLOYER_COMPONENT, "LIR", formula="total_working_hours * .4046"),
}


def install_custom_fields() -> None:
	"""Create or update the app-owned payroll fields and components."""
	initialize_existing_earnings = not frappe.db.exists("Custom Field", SOCIAL_SECURITY_TAXABLE_CUSTOM_FIELD)
	create_custom_fields(get_custom_fields(), update=True)
	if initialize_existing_earnings:
		enable_social_security_for_existing_earnings()
	install_salary_components()


def install_salary_components() -> None:
	"""Create required app-owned Salary Components without changing existing configuration."""
	for component, values in COMPONENTS.items():
		if frappe.db.exists("Salary Component", component):
			continue

		frappe.get_doc(
			{
				"doctype": "Salary Component",
				**values,
			}
		).insert(ignore_permissions=True)


def enable_social_security_for_existing_earnings() -> None:
	"""Apply the default-on policy once to earning components that predate the field."""
	frappe.db.set_value(
		"Salary Component",
		{"type": "Earning"},
		"us_social_security_taxable",
		1,
		update_modified=False,
	)


def uninstall_custom_fields() -> None:
	"""Remove the app-owned payroll fields during app uninstall."""
	delete_custom_fields(get_custom_fields())
