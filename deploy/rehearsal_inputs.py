"""Prepare private, disposable empty-site rehearsal inputs from locally cached images."""

import json
import os
import secrets
import subprocess
from pathlib import Path

os.umask(0o077)
path = Path(".local/rehearsal.env")
if path.exists():
	raise SystemExit("Rehearsal inputs already exist; retaining them unchanged")
images = {}
for key, image in [
	("FRAPPE_IMAGE", "cranescastle-frappe:rehearsal"),
	("MARIADB_IMAGE", "mariadb:10.8"),
	("REDIS_IMAGE", "redis:alpine"),
]:
	item = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
	images[key] = item["RepoDigests"][0] if item.get("RepoDigests") else item["Id"]
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(
	"".join(f"{key}={value}\n" for key, value in images.items())
	+ "FRAPPE_SITE=frappe.cranescastle.test\n"
	+ "MARIADB_ROOT_PASSWORD="
	+ secrets.token_hex(24)
	+ "\n"
	+ "FRAPPE_ADMIN_PASSWORD="
	+ secrets.token_hex(24)
	+ "\n"
)
print("Created private rehearsal inputs; no containers started and no source data read.")
