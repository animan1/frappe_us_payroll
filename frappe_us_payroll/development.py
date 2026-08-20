import frappe

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

from frappe_us_payroll.payroll.social_security import SOCIAL_SECURITY_COMPONENT

DEMO_COMPANY = "Crane's Castle Brewing"
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
	existing_employee = frappe.db.get_value(
		"Employee",
		{"employee_name": DEMO_EMPLOYEE_NAME, "company": DEMO_COMPANY},
		"name",
	)
	if isinstance(existing_employee, str):
		return existing_employee

	employee = frappe.get_doc(
		{
			"doctype": "Employee",
			"first_name": DEMO_EMPLOYEE_NAME,
			"company": DEMO_COMPANY,
			"gender": "Female",
			"date_of_birth": "1990-01-01",
			"date_of_joining": "2026-01-01",
			"status": "Active",
		}
	).insert(ignore_permissions=True)
	return employee.name


def _ensure_holiday_assignment(employee: str, holiday_list: str) -> None:
	filters: dict[str, str | int] = {
		"applicable_for": "Employee",
		"assigned_to": employee,
		"docstatus": 1,
	}
	if frappe.db.exists("Holiday List Assignment", filters):
		return

	assignment = frappe.get_doc(
		{
			"doctype": "Holiday List Assignment",
			"applicable_for": "Employee",
			"assigned_to": employee,
			"holiday_list": holiday_list,
			"from_date": "2026-01-01",
		}
	).insert(ignore_permissions=True)
	assignment.submit()


def _ensure_salary_structure() -> None:
	if frappe.db.exists("Salary Structure", DEMO_STRUCTURE):
		return

	structure = frappe.get_doc(
		{
			"doctype": "Salary Structure",
			"name": DEMO_STRUCTURE,
			"company": DEMO_COMPANY,
			"currency": "USD",
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
	).insert(ignore_permissions=True)
	structure.submit()


def _ensure_salary_structure_assignment(employee: str) -> None:
	filters: dict[str, str | int] = {
		"employee": employee,
		"salary_structure": DEMO_STRUCTURE,
		"docstatus": 1,
	}
	if frappe.db.exists("Salary Structure Assignment", filters):
		return

	assignment = frappe.get_doc(
		{
			"doctype": "Salary Structure Assignment",
			"employee": employee,
			"salary_structure": DEMO_STRUCTURE,
			"company": DEMO_COMPANY,
			"currency": "USD",
			"from_date": "2026-01-01",
			"base": 1000,
		}
	).insert(ignore_permissions=True)
	assignment.submit()
