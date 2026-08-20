from frappe_us_payroll.payroll.components import SalarySlipDeductions


def apply_us_payroll_deductions(salary_slip: SalarySlipDeductions) -> None:
	"""Reserve HRMS's regional deduction hook for the production US adapter."""
	return None
