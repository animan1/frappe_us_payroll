from decimal import Decimal

import frappe

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

from frappe_us_payroll.payroll.social_security import SOCIAL_SECURITY_COMPONENT
from frappe_us_payroll.payroll.salary_slip import FIT_COMPONENT
from frappe_us_payroll.setup import (
	COMPONENTS,
	LI_EMPLOYEE_COMPONENT,
	MEDICARE_COMPONENT,
	PFML_COMPONENT,
	TIPS_PAID_COMPONENT,
	WA_CARES_COMPONENT,
)

DEMO_COMPANY = "Demo Company"
DEMO_EMPLOYEE_NAME = "US Payroll E2E Employee"
DEMO_STRUCTURE = "US Payroll E2E Salary Structure"
DEMO_POSTING_DATE = "2026-08-20"


def recalculate_salary_slip(salary_slip_name: str) -> str:
	"""Recalculate and save an existing draft Salary Slip for UI testing."""
	salary_slip = frappe.get_doc("Salary Slip", salary_slip_name)
	salary_slip.save(ignore_permissions=True)
	return salary_slip.name


def ensure_social_security_e2e_demo() -> str:
	"""Create an idempotent, persistent Salary Slip for manual UI review."""
	holiday_list = _ensure_holiday_list()
	employee = _ensure_employee()
	_ensure_holiday_assignment(employee, holiday_list)
	_ensure_salary_structure()
	_ensure_salary_structure_assignment(employee)

	existing_slip = frappe.db.get_value(
		"Salary Slip",
		{"employee": employee, "salary_structure": DEMO_STRUCTURE, "docstatus": 0},
		"name",
	)
	if isinstance(existing_slip, str):
		return existing_slip

	previous_country = frappe.flags.country
	frappe.flags.country = "United States"
	try:
		salary_slip = make_salary_slip(
			DEMO_STRUCTURE,
			employee=employee,
			posting_date=DEMO_POSTING_DATE,
		)
		salary_slip.insert(ignore_permissions=True)
		return salary_slip.name
	finally:
		frappe.flags.country = previous_country


def _ensure_holiday_list() -> str:
	name = "US Payroll E2E 2026"
	if not frappe.db.exists("Holiday List", name):
		frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": name,
				"from_date": "2026-01-01",
				"to_date": "2026-12-31",
			}
		).insert(ignore_permissions=True)
	return name


def _ensure_employee() -> str:
	try:
		existing_employee = frappe.get_doc(
			"Employee",
			{
				"employee_name": DEMO_EMPLOYEE_NAME,
				"company": DEMO_COMPANY,
			},
		)
		return existing_employee
	except frappe.exceptions.DoesNotExistError:
		pass

	employee = frappe.get_doc(
		{
			"doctype": "Employee",
			"first_name": DEMO_EMPLOYEE_NAME,
			"company": DEMO_COMPANY,
			"gender": "Female",
			"date_of_birth": "1990-01-01",
			"date_of_joining": "2026-01-01",
			"status": "Active",
			"us_w4_filing_status": "Single or Married filing separately",
		}
	)
	employee.insert(ignore_permissions=True)
	return employee


def _ensure_holiday_assignment(employee: str, holiday_list: str) -> None:
	filters: dict[str, str | int] = {
		"applicable_for": "Employee",
		"assigned_to": employee.name,
		"docstatus": 1,
	}
	if frappe.db.exists("Holiday List Assignment", filters):
		return

	assignment = frappe.get_doc(
		{
			"doctype": "Holiday List Assignment",
			"applicable_for": "Employee",
			"assigned_to": employee.name,
			"holiday_list": holiday_list,
			"from_date": "2026-01-01",
		}
	).insert(ignore_permissions=True)
	assignment.submit()


def _component_to_structure(comp_name):
	comp = dict(COMPONENTS[comp_name])
	comp["abbr"] = comp.pop("salary_component_abbr")
	return {"amount": 0, "depends_on_payment_days": 0, **comp}


def _ensure_salary_structure() -> None:
	if frappe.db.exists("Salary Structure", DEMO_STRUCTURE):
		print(frappe.get_doc("Salary Structure", DEMO_STRUCTURE))
		return

	structure = frappe.get_doc(
		{
			"doctype": "Salary Structure",
			"name": DEMO_STRUCTURE,
			"company": DEMO_COMPANY,
			"currency": "USD",
			"payroll_frequency": "Fortnightly",
			"is_active": "Yes",
			"salary_slip_based_on_timesheet": 1,
			"hour_rate": 17.13,
			"salary_component": "Basic",
			"earnings": [
				{
					"salary_component": "Basic",
					"abbr": "B",
					"amount": 0,
					"depends_on_payment_days": 0,
				},
				{
					"salary_component": "Tips",
					"abbr": "T",
					"amount": 0,
					"depends_on_payment_days": 0,
				},
			],
			"deductions": [
				{
					"salary_component": SOCIAL_SECURITY_COMPONENT,
					"abbr": "USSS",
					"amount": 0,
					"depends_on_payment_days": 0,
				},
				{
					"salary_component": FIT_COMPONENT,
					"abbr": "FIT",
					"amount": 0,
					"depends_on_payment_days": 0,
				},
				{
					"salary_component": MEDICARE_COMPONENT,
					"abbr": "Med",
					"amount": 0,
					"depends_on_payment_days": 0,
					"amount_based_on_formula": 1,
					"formula": "gross_pay * .0145",
				},
				_component_to_structure(LI_EMPLOYEE_COMPONENT),
				_component_to_structure(WA_CARES_COMPONENT),
				_component_to_structure(PFML_COMPONENT),
				_component_to_structure(TIPS_PAID_COMPONENT),
			],
		}
	).insert(ignore_permissions=True)
	structure.submit()


def _ensure_salary_structure_assignment(employee: str) -> None:
	filters: dict[str, str | int] = {
		"employee": employee.name,
		"salary_structure": DEMO_STRUCTURE,
		"docstatus": 1,
	}
	if frappe.db.exists("Salary Structure Assignment", filters):
		return

	assignment = frappe.get_doc(
		{
			"doctype": "Salary Structure Assignment",
			"employee": employee.name,
			"salary_structure": DEMO_STRUCTURE,
			"company": DEMO_COMPANY,
			"currency": "USD",
			"from_date": "2026-01-01",
			"base": 1000,
			"us_social_security_taxable_wages_till_date": 5206.31,
		}
	).insert(ignore_permissions=True)
	assignment.submit()


def _ensure_doc(doctype, name, values):
	if frappe.db.exists(doctype, name):
		return frappe.get_doc(doctype, name)

	frappe.get_doc(
		{
			"doctype": doctype,
			"name": name,
			**values,
		}
	).insert(ignore_permissions=True)


def _seed_tips(employee):
	doc_type = "Additional Salary"
	payroll_date = "2026-08-15"
	amount = Decimal("288.98")
	payload = {
		"employee": employee.name,
		"salary_component": "Tips",
		"payroll_date": payroll_date,
	}
	existing = frappe.db.exists(doc_type, {"docstatus": ("!=", 2), **payload})
	if existing:
		return frappe.get_doc("Additional Salary", existing)

	doc = frappe.get_doc(
		{
			"doctype": doc_type,
			"company": DEMO_COMPANY,
			"employee_name": employee.employee_name,
			"amount": amount,
			"overwrite_salary_structure_amount": 0,
			**payload,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()

	return doc


def _ensure_setup_complete():
	if frappe.is_setup_complete():
		return

	setup_complete(
		{
			"language": "English",
			"email": "admin@example.com",
			"full_name": "Administrator",
			"password": "Administrator",
			"country": "United States",
			"timezone": "America/Los_Angeles",
			"currency": "USD",
			"enable_telemetry": 0,
			"fy_start_date": "2026-01-01",
			"fy_end_date": "2026-12-31",
			"company_name": DEMO_COMPANY,
			"company_abbr": "D",
		}
	)


def _seed_company():
	_ensure_doc(
		"Company",
		DEMO_COMPANY,
		{
			"abbr": "D",
			"default_currency": "USD",
			"country": "United States",
			"company_name": DEMO_COMPANY,
		},
	)


def _seed_salary_components():
	doc_type = "Salary Component"
	tips_comp = "Tips"
	_ensure_doc(
		doc_type,
		tips_comp,
		{
			"salary_component": tips_comp,
			"type": "Earning",
			"is_tax_applicable": 1,
			"depends_on_payment_days": 0,
			"us_social_security_taxable": 1,
		},
	)
	for ded in (SOCIAL_SECURITY_COMPONENT, FIT_COMPONENT, MEDICARE_COMPONENT):
		print(
			_ensure_doc(
				doc_type,
				ded,
				{
					"salary_component": ded,
					"type": "Deduction",
				},
			).__dict__
		)


def _seed_timesheet(employee):
	if frappe.db.exists(
		"Timesheet",
		{
			"employee": employee.name,
		},
	):
		return
	activity_type = "Execution"
	doc = frappe.get_doc(
		{
			"doctype": "Timesheet",
			"employee": employee.name,
			"time_logs": [
				{
					"activity_type": activity_type,
					"from_time": "2026-08-03 16:00:00",
					"to_time": "2026-08-03 23:00:00",
					"hours": 7,
				},
				{
					"activity_type": activity_type,
					"from_time": "2026-08-06 12:00:00",
					"to_time": "2026-08-06 21:30:00",
					"hours": 9.5,
				},
				{
					"activity_type": activity_type,
					"from_time": "2026-08-08 13:00:00",
					"to_time": "2026-08-08 21:00:00",
					"hours": 8,
				},
			],
		}
	)

	doc.insert(ignore_permissions=True)
	doc.submit()


def seed():
	_ensure_setup_complete()
	_seed_company()
	_seed_salary_components()
	_ensure_salary_structure()
	holiday_list = _ensure_holiday_list()
	employee = _ensure_employee()
	_ensure_holiday_assignment(employee, holiday_list)
	_ensure_salary_structure_assignment(employee)
	_seed_timesheet(employee)
	_seed_tips(employee)

	frappe.db.commit()
