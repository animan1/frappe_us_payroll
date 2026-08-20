from collections.abc import Mapping
from datetime import date
from typing import NoReturn, Protocol, TypeAlias, overload

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list[JsonValue] | dict[str, JsonValue]

class _Config(Protocol):
	def get(self, key: str, default: bool | None = ...) -> bool | None: ...

class _Database(Protocol):
	def exists(self, doctype: str, name: str | Mapping[str, JsonScalar]) -> bool: ...
	def get_value(
		self,
		doctype: str,
		filters: str | Mapping[str, JsonScalar],
		fieldname: str,
	) -> JsonScalar: ...
	def get_single_value(self, doctype: str, fieldname: str) -> JsonScalar: ...
	def set_single_value(self, doctype: str, fieldname: str, value: JsonScalar) -> None: ...
	def set_value(
		self,
		doctype: str,
		filters: Mapping[str, JsonScalar],
		fieldname: str,
		value: JsonScalar,
		*,
		update_modified: bool = ...,
	) -> None: ...

class _Document(Protocol):
	name: str
	def insert(self, *, ignore_permissions: bool = ...) -> _Document: ...
	def save(self, *, ignore_permissions: bool = ...) -> _Document: ...
	def submit(self) -> _Document: ...

class _Flags(Protocol):
	country: str | None

class ValidationError(Exception): ...

conf: _Config
db: _Database
flags: _Flags

@overload
def get_doc(values: Mapping[str, JsonValue]) -> _Document: ...
@overload
def get_doc(doctype: str, name: str) -> _Document: ...
def get_all(
	doctype: str,
	*,
	filters: Mapping[
		str,
		JsonScalar | tuple[str, JsonScalar] | tuple[str, tuple[date, date]],
	]
	| None = ...,
	pluck: str,
) -> list[JsonScalar]: ...
def throw(message: str, *, exc: type[Exception], title: str | None = ...) -> NoReturn: ...
