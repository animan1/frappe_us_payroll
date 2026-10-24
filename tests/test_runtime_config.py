import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("runtime", Path("deploy/runtime.py"))
assert spec is not None and spec.loader is not None
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeConfigurationTests(unittest.TestCase):
	def test_requires_private_file_and_digest_images(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "production.env"
			text = "".join(
				f"{key}=example/{key.lower()}@sha256:" + "a" * 64 + "\n"
				for key in ("FRAPPE_IMAGE", "MARIADB_IMAGE", "REDIS_IMAGE")
			)
			text += "FRAPPE_SITE=restored.example.test\nMARIADB_ROOT_PASSWORD=" + "x" * 32 + "\n"
			path.write_text(text)
			path.chmod(0o644)
			with self.assertRaisesRegex(ValueError, "0600"):
				runtime.configuration(path)
			path.chmod(0o600)
			self.assertEqual(runtime.configuration(path)["FRAPPE_SITE"], "restored.example.test")
			path.write_text(text.replace("@sha256:" + "a" * 64, ":latest"))
			with self.assertRaisesRegex(ValueError, "immutable"):
				runtime.configuration(path)

	def test_rejects_duplicate_inputs(self) -> None:
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / "production.env"
			path.write_text("FRAPPE_IMAGE=one\nFRAPPE_IMAGE=two\n")
			path.chmod(0o600)
			with self.assertRaisesRegex(ValueError, "Duplicate"):
				runtime.configuration(path)
