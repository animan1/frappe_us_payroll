from collections.abc import Mapping
from typing import NoReturn, Protocol, TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None

class _Config(Protocol):
	def get(self, key: str, default: bool | None = ...) -> bool | None: ...

class _Database(Protocol):
	def exists(self, doctype: str, name: str) -> bool: ...

class _Document(Protocol):
	def insert(self, *, ignore_permissions: bool = ...) -> _Document: ...

class ValidationError(Exception): ...

conf: _Config
db: _Database

def get_doc(values: Mapping[str, JsonScalar]) -> _Document: ...
def throw(message: str, *, exc: type[Exception], title: str | None = ...) -> NoReturn: ...
