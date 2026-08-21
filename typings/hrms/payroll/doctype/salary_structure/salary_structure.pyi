from typing import Protocol

class _SalarySlip(Protocol):
	name: str

	def insert(self, *, ignore_permissions: bool = ...) -> _SalarySlip: ...

def make_salary_slip(
	source_name: str,
	*,
	employee: str,
	posting_date: str,
) -> _SalarySlip: ...
