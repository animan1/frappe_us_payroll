"""Restore a checksummed rehearsal snapshot only over our freshly initialized site."""

import hashlib
import json
import os
import subprocess
import tarfile
from pathlib import Path

import frappe
from frappe.commands.site import _restore

site = os.environ["FRAPPE_SITE"]
target = Path("sites").resolve() / site
marker = target / ".empty-rehearsal"
if not marker.exists():
	raise SystemExit("Refusing restore: destination is not a fresh empty rehearsal site")
backup = Path("/backup")
manifest = json.loads((backup / "manifest.json").read_text())
if set(manifest["files"]) != {"database.sql.gz", "site-files.tar.gz"}:
	raise SystemExit("Unexpected backup inventory")
for name, evidence in manifest["files"].items():
	path = backup / name
	with path.open("rb") as source:
		if hashlib.file_digest(source, "sha256").hexdigest() != evidence["sha256"]:
			raise SystemExit("Backup checksum mismatch")
with tarfile.open(backup / "site-files.tar.gz") as archive:
	members = archive.getmembers()
	for member in members:
		name = member.name.rstrip("/")
		if (
			not (member.isfile() or member.isdir())
			or member.issym()
			or member.islnk()
			or not (
				name == "site_config.json"
				or name in ("public/files", "private/files")
				or name.startswith(("public/files/", "private/files/"))
			)
			or ".." in Path(name).parts
		):
			raise SystemExit("Unsafe archive member")
	source_config = json.load(archive.extractfile("site_config.json"))
	os.chdir(target.parent)
	frappe.init(site=site)
	_restore(
		site=site,
		sql_file_path=str(backup / "database.sql.gz"),
		db_root_username="root",
		db_root_password=os.environ["MARIADB_ROOT_PASSWORD"],
		admin_password=os.environ["FRAPPE_ADMIN_PASSWORD"],
		force=True,
	)
	frappe.destroy()
	# Keep destination DB connection credentials; retain only the original encryption keys.
	destination = json.loads((target / "site_config.json").read_text())
	for key in ("encryption_key", "backup_encryption_key"):
		if key in source_config:
			destination[key] = source_config[key]
	destination.update(mute_emails=1, pause_scheduler=1, developer_mode=0)
	(target / "site_config.json").write_text(json.dumps(destination))
	archive.extractall(target, members=[m for m in members if m.name != "site_config.json"], filter="data")
for directory in (target, target.parent.parent / "logs"):
	for path in [directory, *directory.rglob("*")]:
		os.chown(path, 1000, 0)
(target / "site_config.json").chmod(0o600)
environment = dict(os.environ, HOME="/home/frappe")
subprocess.run(
	["bench", "--site", site, "migrate"],
	cwd=target.parent.parent,
	env=environment,
	user=1000,
	group=0,
	check=True,
)
marker.unlink(missing_ok=True)
print("Backup restored into isolated destination; source unchanged, outbound networking remains blocked.")
