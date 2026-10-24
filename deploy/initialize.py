"""Create an empty rehearsal site; never restore over or replace an existing site."""

import json
import os
import socket
import time
from pathlib import Path

import frappe
from frappe.installer import _new_site

site = os.environ["FRAPPE_SITE"]
root = Path("sites").resolve()
if (root / site).exists():
	raise SystemExit("Site already exists; refusing to replace it")
for host, port in [("db", 3306), ("redis-cache", 6379), ("redis-queue", 6379)]:
	for _attempt in range(60):
		try:
			socket.create_connection((host, port), timeout=2).close()
			break
		except OSError:
			time.sleep(1)
	else:
		raise SystemExit("Dependency did not become reachable: " + host)
common = dict(
	db_host="db",
	db_port=3306,
	redis_cache="redis://redis-cache:6379",
	redis_queue="redis://redis-queue:6379",
	redis_socketio="redis://redis-queue:6379",
	socketio_port=9000,
	pause_scheduler=1,
	mute_emails=1,
)
(root / "common_site_config.json").write_text(json.dumps(common))
(root / "apps.txt").write_text("frappe\nerpnext\nhrms\nfrappe_us_payroll\n")
os.chdir(root)
frappe.init(site, new_site=True)
_new_site(
	db_name=None,
	site=site,
	db_root_username="root",
	db_root_password=os.environ["MARIADB_ROOT_PASSWORD"],
	admin_password=os.environ["FRAPPE_ADMIN_PASSWORD"],
	db_type="mariadb",
	db_host="db",
	db_port=3306,
	mariadb_user_host_login_scope="%",
	install_apps=["erpnext", "hrms", "frappe_us_payroll"],
)
frappe.destroy()
(root / site / ".empty-rehearsal").touch()
print("Empty isolated site created; scheduler and mail are disabled.")
