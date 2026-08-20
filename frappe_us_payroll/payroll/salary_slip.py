def apply_us_payroll_deductions(salary_slip) -> None:
	"""Apply US deductions before HRMS finalizes Salary Slip totals.

	The extension point is wired before the first federal calculator is added.
	Keeping it inert avoids shipping a test deduction as production behavior.
	"""
	return None


def set_deduction_amount(salary_slip, component_name: str, amount) -> bool:
	"""Set an existing deduction row and report whether it was found."""
	for deduction in salary_slip.get("deductions") or ():
		if deduction.salary_component == component_name:
			deduction.amount = amount
			deduction.default_amount = amount
			return True

	return False
