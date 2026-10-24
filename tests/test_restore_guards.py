import io
import json
import os
import runpy
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch


class RestoreGuards(TestCase):
	def test_existing_destination_without_empty_marker_is_never_restored(self) -> None:
		frappe = MagicMock()
		site = MagicMock()
		with (
			patch.dict("sys.modules", {"frappe": frappe, "frappe.commands.site": site}),
			patch.dict(os.environ, FRAPPE_SITE="restored.example.test"),
			patch.object(Path, "exists", return_value=False),
			self.assertRaisesRegex(SystemExit, "not a fresh empty"),
		):
			runpy.run_path("deploy/restore.py")
		site._restore.assert_not_called()

	def test_modified_backup_is_refused_before_database_restore(self) -> None:
		frappe = MagicMock()
		site = MagicMock()
		manifest = {
			"files": {name: {"sha256": "0" * 64} for name in ("database.sql.gz", "site-files.tar.gz")}
		}
		with (
			patch.dict("sys.modules", {"frappe": frappe, "frappe.commands.site": site}),
			patch.dict(os.environ, FRAPPE_SITE="restored.example.test"),
			patch.object(Path, "exists", return_value=True),
			patch.object(Path, "read_text", return_value=json.dumps(manifest)),
			patch.object(Path, "open", return_value=io.BytesIO(b"changed archive")),
			self.assertRaisesRegex(SystemExit, "checksum mismatch"),
		):
			runpy.run_path("deploy/restore.py")
		site._restore.assert_not_called()
