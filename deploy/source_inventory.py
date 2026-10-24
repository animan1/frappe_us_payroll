"""Read-only source metadata; never print site configuration or database records."""

import json
import subprocess
from pathlib import Path

root = Path("/home/frappe/frappe-bench")
apps = {}
for app in ("frappe", "erpnext", "hrms", "frappe_us_payroll"):
	path = root / "apps" / app
	apps[app] = {
		"revision": subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip(),
		"dirty": bool(
			subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True).strip()
		),
		"changed_paths": subprocess.check_output(
			["git", "-C", str(path), "status", "--porcelain"], text=True
		).splitlines(),
	}
site = root / "sites/frappe-us-payroll.localhost"
backups = site / "private/backups"
print(
	json.dumps(
		dict(
			apps=apps,
			backups=[
				dict(name=p.name, bytes=p.stat().st_size) for p in sorted(backups.glob("*")) if p.is_file()
			],
			site_config_present=(site / "site_config.json").is_file(),
		),
		indent=2,
	)
)
