import importlib.util
import io
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from frappe_us_payroll.payroll.component_names import FEDERAL_INCOME_TAX


def load_importer() -> types.ModuleType:
	path = Path(__file__).parents[1] / "scripts" / "import_timetrex_ytd.py"
	spec = importlib.util.spec_from_file_location("test_timetrex_importer", path)
	if spec is None or spec.loader is None:
		raise AssertionError("Could not load TimeTrex importer")
	module = importlib.util.module_from_spec(spec)
	sys.modules[spec.name] = module
	with patch.dict(sys.modules, {"frappe": types.ModuleType("frappe")}):
		spec.loader.exec_module(module)
	return module


IMPORTER = load_importer()


class TimeTrexImporterTest(unittest.TestCase):
	def test_reads_redirected_stdin_without_seeking(self) -> None:
		export = "\t".join(
			[
				"First Name",
				"Last Name",
				"Total Gross",
				"Total Deductions",
				"Net Pay",
				"Earning - Regular Time",
				"EE Ded - US - Federal Income Tax",
				"EE Ded - Personal Expense Reimbursement",
				"Pay Period",
			]
		)
		export += "\n" + "\t".join(
			["Test", "Employee", "100", "12", "88", "100", "10", "2", "08/16/2026 -> 08/29/2026"]
		)

		with patch.object(sys, "stdin", io.StringIO(export)):
			totals = IMPORTER.read_totals("-", 2026, date(2026, 8, 29))

		self.assertEqual(len(totals), 1)
		self.assertEqual(totals[0].gross, Decimal("100.00"))
		self.assertEqual(totals[0].deductions, Decimal("12.00"))

	def test_ignored_reimbursement_is_not_written_to_opening_slip(self) -> None:
		components = {
			("earnings", "Regular Time"): Decimal("100.00"),
			("deductions", "US - Federal Income Tax"): Decimal("10.00"),
			("deductions", "Personal Expense Reimbursement"): Decimal("2.00"),
		}

		combined = IMPORTER.combine_components(components)
		gross, deductions, net = IMPORTER.imported_totals(combined)

		self.assertEqual(combined[("deductions", FEDERAL_INCOME_TAX)], Decimal("10.00"))
		self.assertNotIn(("deductions", "Personal Expense Reimbursement"), combined)
		self.assertEqual((gross, deductions, net), (Decimal("100.00"), Decimal("10.00"), Decimal("90.00")))

	def test_unknown_nonzero_component_fails_closed(self) -> None:
		with self.assertRaisesRegex(ValueError, "No Frappe Salary Component mapping"):
			IMPORTER.combine_components({("deductions", "Mystery Tax"): Decimal("1.00")})


if __name__ == "__main__":
	unittest.main()
