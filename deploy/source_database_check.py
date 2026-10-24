"""Check backup viability using the existing development DB administrator, without writes."""

import json
import subprocess
import sys

config = json.load(sys.stdin)
service = config["services"]["mariadb"]
password = service["environment"].get("MYSQL_ROOT_PASSWORD") or service["environment"].get(
	"MARIADB_ROOT_PASSWORD"
)
if not password:
	raise SystemExit("No existing development DB administrator credential found")
code = (
	"root_password = "
	+ repr(password)
	+ "\n"
	+ """
import json
from pathlib import Path
import MySQLdb
root = Path('sites')
site = json.loads((root / 'frappe-us-payroll.localhost/site_config.json').read_text())
common = json.loads((root / 'common_site_config.json').read_text())
try:
    connection = MySQLdb.connect(host=site.get('db_host') or common.get('db_host') or 'mariadb',
                                user='root', passwd=root_password)
    cursor = connection.cursor()
    cursor.execute('SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s',
                   (site['db_name'],))
    exists = bool(cursor.fetchone()[0])
    cursor.execute('SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s', (site['db_name'],))
    tables = cursor.fetchone()[0]
    connection.close()
    print(json.dumps(dict(source_database_exists=exists, source_table_count=tables)))
except MySQLdb.Error:
    raise SystemExit('Read-only administrator check failed; no credentials printed or database changes made')
"""
)
subprocess.run(
	[
		"docker",
		"exec",
		"-i",
		"--workdir",
		"/home/frappe/frappe-bench",
		config["name"] + "-frappe-1",
		"env/bin/python",
		"-",
	],
	input=code,
	text=True,
	check=True,
)
