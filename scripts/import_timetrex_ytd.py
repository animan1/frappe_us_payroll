#!/usr/bin/env python3
"""Import TimeTrex payroll rows as exact, submitted opening Salary Slips.

Stream an export from the host into Docker without copying it, for example:

    make ytd-preview TAX_YEAR=2026 THROUGH_DATE=2026-08-29 < timetrex.csv
    make ytd-import TAX_YEAR=2026 THROUGH_DATE=2026-08-29 < timetrex.csv

The default is a read-only preview. Add ``--apply`` to insert the opening slips.
Rerun with ``--apply --replace`` to replace only slips previously created by
this script. Every mapped Salary Component must already exist with the expected
type; this importer never creates payroll configuration.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
from collections import defaultdict
from collections.abc import Iterable
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, TextIO, cast

import frappe

from frappe_us_payroll.payroll.component_names import (
	FEDERAL_INCOME_TAX,
	FUTA_EMPLOYER,
	MEDICARE_EMPLOYEE,
	MEDICARE_EMPLOYER,
	SOCIAL_SECURITY_EMPLOYEE,
	SOCIAL_SECURITY_EMPLOYER,
	WA_CARES_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYEE,
	WA_INDUSTRIAL_INSURANCE_EMPLOYER,
	WA_PAID_LEAVE_EMPLOYEE,
	WA_PAID_LEAVE_EMPLOYER,
	WA_UNEMPLOYMENT_EMPLOYER,
)

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
FIRST_NAME = "First Name"
LAST_NAME = "Last Name"
PAY_PERIOD = "Pay Period"
TOTAL_GROSS = "Total Gross"
TOTAL_DEDUCTIONS = "Total Deductions"
NET_PAY = "Net Pay"

CATEGORY_PREFIXES = {
	"Earning - ": "earnings",
	"EE Ded - ": "deductions",
	"ER Ded - ": "employer_contributions",
}

# Exhaustive mapping from the known TimeTrex export columns to the current
# Frappe payroll configuration. Unknown nonzero components are rejected.
COMPONENT_MAPPINGS = {
	("earnings", "Regular Time"): "Basic",
	("earnings", "Regular Time - Brewery"): "Basic",
	("earnings", "Over Time"): "Basic",
	("earnings", "Over Time - Brewery"): "Basic",
	("earnings", "Tips"): "Tips",
	("deductions", "US - Federal Income Tax"): FEDERAL_INCOME_TAX,
	("deductions", "Social Security (FICA)"): SOCIAL_SECURITY_EMPLOYEE,
	("deductions", "Medicare"): MEDICARE_EMPLOYEE,
	("deductions", "WA - L&I - Employee (Brewery)"): WA_INDUSTRIAL_INSURANCE_EMPLOYEE,
	("deductions", "WA - L&I - Employee (Taproom)"): WA_INDUSTRIAL_INSURANCE_EMPLOYEE,
	("deductions", "WA - WA Cares"): WA_CARES_EMPLOYEE,
	("deductions", "WA - Paid Family and Medical Leave - Employee"): WA_PAID_LEAVE_EMPLOYEE,
	("deductions", "Tips Already Paid"): "Tips Already Paid",
	("deductions", "Child Support"): "Child Support",
	("deductions", "Garnishment"): "Garnishment",
	("employer_contributions", "Social Security (FICA)"): SOCIAL_SECURITY_EMPLOYER,
	("employer_contributions", "US - Federal Unemployment Insurance"): FUTA_EMPLOYER,
	("employer_contributions", "Medicare"): MEDICARE_EMPLOYER,
	("employer_contributions", "WA - L&I - Employer"): WA_INDUSTRIAL_INSURANCE_EMPLOYER,
	("employer_contributions", "WA - Workers Compensation - Employer"): (WA_INDUSTRIAL_INSURANCE_EMPLOYER),
	("employer_contributions", "WA - Unemployment Insurance"): WA_UNEMPLOYMENT_EMPLOYER,
	("employer_contributions", "WA - Industrial Insurance"): WA_INDUSTRIAL_INSURANCE_EMPLOYER,
	("employer_contributions", "WA - Paid Family and Medical Leave - Employer"): WA_PAID_LEAVE_EMPLOYER,
}

# This was a one-off TimeTrex deduction and has no continuing YTD effect. Exclude
# it from both the opening slip's component rows and its aggregate deductions.
IGNORED_COMPONENTS = {
	("deductions", "Personal Expense Reimbursement"),
}


@dataclass
class EmployeeTotals:
	first_name: str
	last_name: str
	through_date: date
	gross: Decimal = ZERO
	deductions: Decimal = ZERO
	net: Decimal = ZERO
	components: dict[tuple[str, str], Decimal] = field(default_factory=lambda: defaultdict(lambda: ZERO))
	row_count: int = 0

	@property
	def source_name(self) -> str:
		return " ".join(part for part in (self.first_name, self.last_name) if part).strip()


def money(value: str | None, *, column: str, row_number: int) -> Decimal:
	text = (value or "").strip()
	if not text:
		return ZERO
	negative = text.startswith("(") and text.endswith(")")
	text = text.strip("()").replace("$", "").replace(",", "")
	try:
		amount = Decimal(text)
	except InvalidOperation as error:
		raise ValueError(f"Row {row_number}: {column!r} is not a monetary value: {value!r}") from error
	if negative:
		amount = -amount
	return amount.quantize(CENT)


def period_end(value: str, *, row_number: int) -> date:
	parts = [part.strip() for part in value.split("->")]
	if len(parts) != 2:
		raise ValueError(f"Row {row_number}: invalid Pay Period {value!r}")
	try:
		return datetime.strptime(parts[1], "%m/%d/%Y").date()
	except ValueError as error:
		raise ValueError(f"Row {row_number}: invalid Pay Period end date {parts[1]!r}") from error


def component_column(header: str) -> tuple[str, str] | None:
	for prefix, parentfield in CATEGORY_PREFIXES.items():
		if header.startswith(prefix):
			return parentfield, header.removeprefix(prefix).strip()
	return None


def read_totals(path: str, tax_year: int, through_date: date) -> list[EmployeeTotals]:
	source_context = (
		nullcontext(sys.stdin) if path == "-" else Path(path).open("r", encoding="utf-8-sig", newline="")
	)
	with source_context as opened_source:
		source = cast(TextIO, opened_source)
		contents = source.read()
		sample = contents[:8192]
		try:
			dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
		except csv.Error as error:
			raise ValueError("Could not determine whether the export is CSV or tab-delimited") from error
		reader = csv.DictReader(io.StringIO(contents), dialect=dialect)
		if reader.fieldnames is None:
			raise ValueError("The export has no header row")
		required = {FIRST_NAME, LAST_NAME, PAY_PERIOD, TOTAL_GROSS, TOTAL_DEDUCTIONS, NET_PAY}
		missing = required.difference(reader.fieldnames)
		if missing:
			raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

		component_headers = [header for header in reader.fieldnames if component_column(header)]
		grouped: dict[tuple[str, str], EmployeeTotals] = {}
		for row_number, row in enumerate(reader, start=2):
			end_date = period_end(row[PAY_PERIOD], row_number=row_number)
			if end_date.year != tax_year or end_date > through_date:
				continue

			first_name = (row[FIRST_NAME] or "").strip()
			last_name = (row[LAST_NAME] or "").strip()
			if not first_name and not last_name:
				raise ValueError(f"Row {row_number}: employee name is blank")

			gross = money(row[TOTAL_GROSS], column=TOTAL_GROSS, row_number=row_number)
			deductions = money(row[TOTAL_DEDUCTIONS], column=TOTAL_DEDUCTIONS, row_number=row_number)
			net = money(row[NET_PAY], column=NET_PAY, row_number=row_number)
			components: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
			for header in component_headers:
				category = component_column(header)
				assert category is not None
				components[category] += money(row[header], column=header, row_number=row_number)

			earnings_total = sum(
				(amount for (parentfield, _), amount in components.items() if parentfield == "earnings"),
				ZERO,
			)
			deductions_total = sum(
				(amount for (parentfield, _), amount in components.items() if parentfield == "deductions"),
				ZERO,
			)
			if earnings_total != gross:
				raise ValueError(
					f"Row {row_number}: earning columns total {earnings_total}, but Total Gross is {gross}"
				)
			if deductions_total != deductions:
				raise ValueError(
					f"Row {row_number}: employee deduction columns total {deductions_total}, "
					f"but Total Deductions is {deductions}"
				)
			if gross - deductions != net:
				raise ValueError(
					f"Row {row_number}: gross {gross} minus deductions {deductions} is "
					f"{gross - deductions}, but Net Pay is {net}"
				)

			key = (first_name.casefold(), last_name.casefold())
			if key not in grouped:
				grouped[key] = EmployeeTotals(first_name, last_name, end_date)
			totals = grouped[key]
			totals.through_date = max(totals.through_date, end_date)
			totals.gross += gross
			totals.deductions += deductions
			totals.net += net
			totals.row_count += 1
			for category, amount in components.items():
				totals.components[category] += amount

	return sorted(grouped.values(), key=lambda totals: totals.source_name.casefold())


def load_employee_map(path: Path | None) -> dict[str, str]:
	if path is None:
		return {}
	values = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(values, dict) or not all(
		isinstance(key, str) and isinstance(value, str) for key, value in values.items()
	):
		raise ValueError("Employee map must be a JSON object mapping TimeTrex names to Frappe Employee IDs")
	return values


def resolve_employee(totals: EmployeeTotals, employee_map: dict[str, str]) -> dict[str, Any]:
	mapped_name = employee_map.get(totals.source_name)
	filters: dict[str, Any] = (
		{"name": mapped_name}
		if mapped_name
		else {"first_name": totals.first_name, "last_name": totals.last_name}
	)
	matches = frappe.get_all(
		"Employee",
		filters=filters,
		fields=["name", "employee_name", "company"],
		limit_page_length=2,
	)
	if len(matches) != 1:
		detail = "no matches" if not matches else "multiple matches"
		raise ValueError(f"Employee {totals.source_name!r}: {detail}; add an exact mapping to --employee-map")
	return dict(matches[0])


def canonical_component(parentfield: str, source_component: str) -> str:
	try:
		return COMPONENT_MAPPINGS[(parentfield, source_component)]
	except KeyError as error:
		raise ValueError(
			f"No Frappe Salary Component mapping for TimeTrex {parentfield} component {source_component!r}"
		) from error


def combine_components(
	components: dict[tuple[str, str], Decimal],
) -> dict[tuple[str, str], Decimal]:
	combined: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
	for (parentfield, source_component), amount in components.items():
		if (parentfield, source_component) in IGNORED_COMPONENTS:
			continue
		component = canonical_component(parentfield, source_component)
		combined[(parentfield, component)] += amount
	return {key: amount for key, amount in combined.items() if amount != ZERO}


def imported_totals(components: dict[tuple[str, str], Decimal]) -> tuple[Decimal, Decimal, Decimal]:
	gross = sum(
		(amount for (parentfield, _), amount in components.items() if parentfield == "earnings"),
		ZERO,
	)
	deductions = sum(
		(amount for (parentfield, _), amount in components.items() if parentfield == "deductions"),
		ZERO,
	)
	return gross, deductions, gross - deductions


def component_type(parentfield: str) -> str:
	return {
		"earnings": "Earning",
		"deductions": "Deduction",
		"employer_contributions": "Employer Contribution",
	}[parentfield]


def require_salary_component(parentfield: str, component: str) -> None:
	existing_type = frappe.db.get_value("Salary Component", component, "type")
	expected_type = component_type(parentfield)
	if not existing_type:
		raise ValueError(
			f"Required {expected_type} Salary Component {component!r} does not exist; "
			"configure it before importing YTD balances"
		)
	if existing_type != expected_type:
		raise ValueError(f"Salary Component {component!r} is {existing_type!r}, expected {expected_type!r}")


def opening_slip_name(employee: str, tax_year: int) -> str:
	return f"TIMETREX-YTD-{tax_year}-{employee}"


def remove_existing_opening_slip(
	name: str,
	employee: str,
	tax_year: int,
	*,
	replace: bool,
) -> None:
	existing = frappe.db.get_value(
		"Salary Slip",
		name,
		["employee", "start_date", "salary_structure", "payroll_entry"],
		as_dict=True,
	)
	if not existing:
		return
	is_script_owned = (
		name == opening_slip_name(employee, tax_year)
		and existing.employee == employee
		and str(existing.start_date) == f"{tax_year}-01-01"
		and not existing.salary_structure
		and not existing.payroll_entry
	)
	if not is_script_owned:
		raise ValueError(f"Refusing to replace unmarked Salary Slip {name!r}")
	if not replace:
		raise ValueError(f"Salary Slip {name!r} already exists; pass --replace to recreate it")
	frappe.db.delete("Salary Detail", {"parent": name, "parenttype": "Salary Slip"})
	frappe.db.delete("Salary Slip", {"name": name})


def insert_opening_slip(
	totals: EmployeeTotals,
	employee: dict[str, Any],
	tax_year: int,
	*,
	replace: bool,
) -> str:
	employee_id = str(employee["name"])
	company = str(employee["company"])
	name = opening_slip_name(employee_id, tax_year)
	components = combine_components(totals.components)
	gross, deductions, net = imported_totals(components)
	for parentfield, component in components:
		require_salary_component(parentfield, component)
	remove_existing_opening_slip(name, employee_id, tax_year, replace=replace)

	currency = frappe.db.get_value("Company", company, "default_currency") or "USD"
	parent_values: dict[str, Any] = {
		"doctype": "Salary Slip",
		"name": name,
		"employee": employee_id,
		"employee_name": employee["employee_name"],
		"company": company,
		"posting_date": totals.through_date,
		"start_date": date(tax_year, 1, 1),
		"end_date": totals.through_date,
		"status": "Submitted",
		"docstatus": 1,
		"currency": currency,
		"exchange_rate": 1,
		"gross_pay": float(gross),
		"base_gross_pay": float(gross),
		"gross_year_to_date": float(gross),
		"base_gross_year_to_date": float(gross),
		"total_deduction": float(deductions),
		"base_total_deduction": float(deductions),
		"net_pay": float(net),
		"base_net_pay": float(net),
		"rounded_total": float(net),
		"base_rounded_total": float(net),
		"year_to_date": float(net),
		"base_year_to_date": float(net),
		"month_to_date": float(net),
		"base_month_to_date": float(net),
	}
	slip = frappe.get_doc(parent_values)
	slip.db_insert()
	for index, ((parentfield, component), amount) in enumerate(sorted(components.items()), start=1):
		row = frappe.get_doc(
			{
				"doctype": "Salary Detail",
				"parent": name,
				"parenttype": "Salary Slip",
				"parentfield": parentfield,
				"idx": index,
				"salary_component": component,
				"amount": float(amount),
				"default_amount": float(amount),
				"year_to_date": float(amount),
			}
		)
		row.db_insert()
	return name


def preview_record(
	totals: EmployeeTotals,
	employee: dict[str, Any],
	tax_year: int,
) -> dict[str, Any]:
	components = combine_components(totals.components)
	gross, deductions, net = imported_totals(components)
	for parentfield, component in components:
		require_salary_component(parentfield, component)
	return {
		"salary_slip": opening_slip_name(str(employee["name"]), tax_year),
		"employee": employee["name"],
		"employee_name": employee["employee_name"],
		"source_name": totals.source_name,
		"rows": totals.row_count,
		"through_date": totals.through_date.isoformat(),
		"gross": str(gross),
		"deductions": str(deductions),
		"net": str(net),
		"components": [
			{"table": parentfield, "component": component, "amount": str(amount)}
			for (parentfield, component), amount in sorted(components.items())
		],
	}


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--site", required=True, help="Frappe site name")
	parser.add_argument(
		"--file",
		required=True,
		help="TimeTrex CSV/TSV path, or - to read it from stdin",
	)
	parser.add_argument("--tax-year", required=True, type=int)
	parser.add_argument("--through-date", required=True, type=date.fromisoformat)
	parser.add_argument(
		"--employee-map",
		type=Path,
		help='Optional JSON object such as {"Export Name": "HR-EMP-00001"}',
	)
	parser.add_argument("--sites-path", default="sites", help="Frappe sites directory")
	parser.add_argument("--apply", action="store_true", help="Insert the opening Salary Slips")
	parser.add_argument(
		"--replace",
		action="store_true",
		help="Replace existing opening slips created by this script (requires --apply)",
	)
	args = parser.parse_args(list(argv))
	if args.replace and not args.apply:
		parser.error("--replace requires --apply")
	if args.through_date.year != args.tax_year:
		parser.error("--through-date must be within --tax-year")
	return args


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
	args = parse_args(argv)
	totals_by_employee = read_totals(args.file, args.tax_year, args.through_date)
	if not totals_by_employee:
		raise ValueError("No TimeTrex rows matched the requested tax year and cutoff")
	employee_map = load_employee_map(args.employee_map)

	sites_path = Path(args.sites_path).resolve()
	os.chdir(sites_path)
	frappe.init(site=args.site, sites_path=".")
	frappe.connect()
	try:
		resolved = [(totals, resolve_employee(totals, employee_map)) for totals in totals_by_employee]
		preview = [preview_record(totals, employee, args.tax_year) for totals, employee in resolved]
		print(json.dumps(preview, indent=2))
		if not args.apply:
			print("Dry run only; rerun with --apply to insert these opening Salary Slips.")
			return 0

		created = [
			insert_opening_slip(totals, employee, args.tax_year, replace=args.replace)
			for totals, employee in resolved
		]
		frappe.db.commit()
		print(f"Created {len(created)} opening Salary Slip(s): {', '.join(created)}")
		return 0
	except Exception:
		frappe.db.rollback()
		raise
	finally:
		frappe.destroy()


if __name__ == "__main__":
	raise SystemExit(main())
