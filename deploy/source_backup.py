"""Capture a private rehearsal backup without changing source database grants."""

import datetime
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

os.umask(0o077)
config = json.load(sys.stdin)
project = config["name"]
site = os.environ.get("BACKUP_SITE") or "frappe-us-payroll.localhost"
if not re.fullmatch(r"[a-z0-9.-]+", site):
	raise SystemExit("Invalid backup site")
backend = "backend" if "backend" in config["services"] else "frappe"
database_service = "db" if "db" in config["services"] else "mariadb"
code = (
	"import json; from pathlib import Path; print(json.loads(Path('sites/"
	+ site
	+ "/site_config.json').read_text())['db_name'])"
)
database = subprocess.check_output(
	[
		"docker",
		"exec",
		"--workdir",
		"/home/frappe/frappe-bench",
		project + "-" + backend + "-1",
		"env/bin/python",
		"-c",
		code,
	],
	text=True,
).strip()
if not re.fullmatch(r"[A-Za-z0-9_]+", database):
	raise SystemExit("Unexpected source database identifier")
directory = Path(".local/backups") / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
directory.mkdir(parents=True, mode=0o700)
# Credentials remain inside the source DB container, never in process arguments or logs.
dump = """set -eu
task_defaults=$(mktemp)
trap 'rm -f "$task_defaults"' EXIT
chmod 600 "$task_defaults"
task_password="${MYSQL_ROOT_PASSWORD:-${MARIADB_ROOT_PASSWORD:-}}"
printf '[client]\nuser=root\npassword=%s\n' "$task_password" > "$task_defaults"
mariadb-dump --defaults-extra-file="$task_defaults" --single-transaction \
    --skip-lock-tables --routines --triggers "$1"
"""
with gzip.open(directory / "database.sql.gz", "wb") as output:
	process = subprocess.Popen(
		["docker", "exec", project + "-" + database_service + "-1", "sh", "-c", dump, "backup", database],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
	)
	assert process.stdout is not None
	while chunk := process.stdout.read(1024 * 1024):
		output.write(chunk)
	_, error = process.communicate()
	if process.returncode:
		raise SystemExit("Database dump failed; partial directory retained privately; no grants changed")
# Archive streams directly to private disk. Never print the site config or file contents.
with (directory / "site-files.tar.gz").open("wb") as output:
	subprocess.run(
		[
			"docker",
			"exec",
			"--workdir",
			"/home/frappe/frappe-bench/sites/" + site,
			project + "-" + backend + "-1",
			"tar",
			"-czf",
			"-",
			"site_config.json",
			"public/files",
			"private/files",
		],
		stdout=output,
		stderr=subprocess.PIPE,
		check=True,
	)
manifest = dict(source_site=site, purpose="rehearsal; source writes were not frozen", files={})
for path in directory.iterdir():
	digest = hashlib.sha256()
	with path.open("rb") as source:
		while chunk := source.read(1024 * 1024):
			digest.update(chunk)
	manifest["files"][path.name] = dict(sha256=digest.hexdigest(), bytes=path.stat().st_size)
(directory / "manifest.json").write_text(json.dumps(manifest, indent=2))
print("Private database/files/config backup captured: " + str(directory))
print("This is a rehearsal snapshot, not a final migration backup; source writes were not frozen.")
