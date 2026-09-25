from collections.abc import Sequence
from typing import Protocol, cast

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from hrms.setup import delete_custom_fields

from frappe_us_payroll.custom_fields import SUPPORTED_JURISDICTIONS, WASHINGTON, get_custom_fields
from frappe_us_payroll.payroll.component_names import (
	FEDERAL_INCOME_TAX,
	FEDERAL_INCOME_TAX_ABBR,
	FUTA_EMPLOYER,
	FUTA_EMPLOYER_ABBR,
	MEDICARE_EMPLOYEE,
	MEDICARE_EMPLOYEE_ABBR,
	MEDICARE_EMPLOYER,
	MEDICARE_EMPLOYER_ABBR,
	SOCIAL_SECURITY_EMPLOYEE,
	SOCIAL_SECURITY_EMPLOYEE_ABBR,
	SOCIAL_SECURITY_EMPLOYER,
	SOCIAL_SECURITY_EMPLOYER_ABBR,
	WA_CARES_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYER,
	WA_PAID_LEAVE_EMPLOYEE,
	WA_PAID_LEAVE_EMPLOYER,
	WA_UNEMPLOYMENT_EMPLOYER,
)

FEDERAL_TAXABLE_EARNING_FIELDS = (
	"us_social_security_taxable",
	"us_federal_income_taxable",
	"us_medicare_taxable",
	"us_futa_taxable",
)
WASHINGTON_TAXABLE_EARNING_FIELDS = (
	"wa_paid_leave_taxable",
	"wa_unemployment_taxable",
)
FEDERAL_SALARY_COMPONENTS = {
	SOCIAL_SECURITY_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": SOCIAL_SECURITY_EMPLOYEE_ABBR,
		"description": "Employee Social Security tax withheld by Frappe US Payroll",
	},
	FEDERAL_INCOME_TAX: {
		"type": "Deduction",
		"salary_component_abbr": FEDERAL_INCOME_TAX_ABBR,
		"description": "Federal income tax withheld by Frappe US Payroll",
	},
	MEDICARE_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": MEDICARE_EMPLOYEE_ABBR,
		"description": "Employee Medicare tax withheld by Frappe US Payroll",
	},
	SOCIAL_SECURITY_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": SOCIAL_SECURITY_EMPLOYER_ABBR,
		"description": "Employer Social Security liability calculated by Frappe US Payroll",
	},
	MEDICARE_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": MEDICARE_EMPLOYER_ABBR,
		"description": "Employer Medicare liability calculated by Frappe US Payroll",
	},
	FUTA_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": FUTA_EMPLOYER_ABBR,
		"description": "Federal unemployment liability calculated by Frappe US Payroll",
	},
}
WASHINGTON_SALARY_COMPONENTS = {
	WA_PAID_LEAVE_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": "WA_PFML_D",
		"description": "Employee WA Paid Leave premium calculated by Frappe US Payroll",
	},
	WA_CARES_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": "WA_Cares",
		"description": "Employee WA Cares premium calculated by Frappe US Payroll",
	},
	WA_INDUSTRIAL_INSURANCE_EMPLOYEE: {
		"type": "Deduction",
		"salary_component_abbr": "WA_LI_D",
		"description": "Employee WA L&I premium calculated by Frappe US Payroll",
	},
	WA_PAID_LEAVE_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "WA_PFML_C",
		"description": "Employer WA Paid Leave liability calculated by Frappe US Payroll",
	},
	WA_INDUSTRIAL_INSURANCE_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "WA_LI_C",
		"description": "Employer WA L&I liability calculated by Frappe US Payroll",
	},
	WA_UNEMPLOYMENT_EMPLOYER: {
		"type": "Employer Contribution",
		"salary_component_abbr": "WA_UI",
		"description": "Employer WA unemployment liability calculated by Frappe US Payroll",
	},
}
JURISDICTION_TAXABLE_EARNING_FIELDS = {
	WASHINGTON: WASHINGTON_TAXABLE_EARNING_FIELDS,
}
JURISDICTION_SALARY_COMPONENTS = {
	WASHINGTON: WASHINGTON_SALARY_COMPONENTS,
}


class JurisdictionRow(Protocol):
	jurisdiction: str


class PayrollSettings(Protocol):
	us_payroll_jurisdictions: Sequence[JurisdictionRow]


def install_custom_fields(doc: object | None = None, method: str | None = None) -> None:
	"""Create or update the app-owned payroll fields and components."""
	# The selection field must exist before a fresh site can choose jurisdictions.
	create_custom_fields(get_custom_fields(), update=True)
	jurisdictions = get_enabled_jurisdictions(doc)
	taxability_fields = list(FEDERAL_TAXABLE_EARNING_FIELDS)
	for jurisdiction in jurisdictions:
		taxability_fields.extend(JURISDICTION_TAXABLE_EARNING_FIELDS[jurisdiction])
	new_taxability_fields = [
		fieldname
		for fieldname in taxability_fields
		if not frappe.db.exists("Custom Field", f"Salary Component-{fieldname}")
	]
	create_custom_fields(get_custom_fields(jurisdictions), update=True)
	for fieldname in new_taxability_fields:
		enable_taxability_for_existing_earnings(fieldname)
	install_salary_components(jurisdictions)


def get_enabled_jurisdictions(doc: object | None = None) -> set[str]:
	"""Return supported jurisdictions selected in Payroll Settings."""
	settings = cast(PayrollSettings, doc if doc is not None else frappe.get_single("Payroll Settings"))
	rows = settings.us_payroll_jurisdictions or ()
	return {row.jurisdiction for row in rows if row.jurisdiction in SUPPORTED_JURISDICTIONS}


def install_salary_components(jurisdictions: set[str]) -> None:
	"""Create required app-owned Salary Components without changing existing configuration."""
	components = dict(FEDERAL_SALARY_COMPONENTS)
	for jurisdiction in jurisdictions:
		components.update(JURISDICTION_SALARY_COMPONENTS[jurisdiction])
	for component_name, values in components.items():
		# Existing components may have live abbreviations, formulas, or account mappings.
		if frappe.db.exists("Salary Component", component_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Salary Component",
				"salary_component": component_name,
				"type": values["type"],
				"depends_on_payment_days": 0,
				"remove_if_zero_valued": 0,
				**values,
			}
		).insert(ignore_permissions=True)


def enable_taxability_for_existing_earnings(fieldname: str) -> None:
	"""Apply a new taxability field's default-on policy to existing earnings."""
	frappe.db.set_value(
		"Salary Component",
		{"type": "Earning"},
		fieldname,
		1,
		update_modified=False,
	)


def enable_social_security_for_existing_earnings() -> None:
	"""Retain the original patch entry point for installed sites."""
	enable_taxability_for_existing_earnings("us_social_security_taxable")


def uninstall_custom_fields() -> None:
	"""Remove the app-owned payroll fields during app uninstall."""
	delete_custom_fields(get_custom_fields(SUPPORTED_JURISDICTIONS))
