from frappe_us_payroll.setup import (
	enable_social_security_for_existing_earnings,
	install_custom_fields,
)


def execute() -> None:
	install_custom_fields()
	enable_social_security_for_existing_earnings()
