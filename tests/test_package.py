import unittest

from frappe_us_payroll import __version__, hooks


class PackageMetadataTest(unittest.TestCase):
	def test_package_and_hook_names_match(self) -> None:
		self.assertEqual(hooks.app_name, "frappe_us_payroll")
		self.assertEqual(__version__, "0.0.1")


if __name__ == "__main__":
	unittest.main()
