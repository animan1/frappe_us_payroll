from collections.abc import Mapping, Sequence

from frappe_us_payroll.custom_fields import CustomFieldValue

def create_custom_fields(
	custom_fields: Mapping[str, Sequence[Mapping[str, CustomFieldValue]]],
	*,
	update: bool = ...,
) -> None: ...
