"""Fail closed before starting the independent production Compose project."""

import os
import re
import stat
import subprocess
import sys
from pathlib import Path


def configuration(path):
	if stat.S_IMODE(path.stat().st_mode) != 0o600:
		raise ValueError("Production env file must have mode 0600")
	values = {}
	for line in path.read_text().splitlines():
		if not line.strip() or line.lstrip().startswith("#"):
			continue
		key, value = line.split("=", 1)
		if key in values:
			raise ValueError("Duplicate configuration key: " + key)
		values[key] = value
	if set(values) != {
		"FRAPPE_IMAGE",
		"MARIADB_IMAGE",
		"REDIS_IMAGE",
		"FRAPPE_SITE",
		"MARIADB_ROOT_PASSWORD",
		"FRAPPE_ADMIN_PASSWORD",
	}:
		raise ValueError("Supply only the six documented runtime inputs")
	for key in ("FRAPPE_IMAGE", "MARIADB_IMAGE", "REDIS_IMAGE"):
		if not re.fullmatch(r"(?:[a-z0-9./:_-]+@)?sha256:[0-9a-f]{64}", values.get(key, "")):
			raise ValueError(key + " must identify an immutable image digest")
	if not re.fullmatch(r"[a-z0-9.-]+", values.get("FRAPPE_SITE", "")):
		raise ValueError("Invalid restored site name")
	if not re.fullmatch(r"[A-Za-z0-9_-]{24,}", values.get("MARIADB_ROOT_PASSWORD", "")):
		raise ValueError("Supply a private random database password: 24+ letters/digits/_/-")
	if not re.fullmatch(r"[A-Za-z0-9_-]{24,}", values.get("FRAPPE_ADMIN_PASSWORD", "")):
		raise ValueError("Supply a private random administrator password: 24+ letters/digits/_/-")
	return values


def main():
	action = sys.argv[1]
	path = Path(os.environ.get("PRODUCTION_ENV") or ".local/production.env").resolve()
	values = configuration(path)
	# Prevent ambient workstation variables from overriding the reviewed private inputs.
	environment = dict(os.environ)
	for key in (
		"FRAPPE_IMAGE",
		"MARIADB_IMAGE",
		"REDIS_IMAGE",
		"FRAPPE_SITE",
		"MARIADB_ROOT_PASSWORD",
		"FRAPPE_ADMIN_PASSWORD",
		"COMPOSE_PROFILES",
		"COMPOSE_FILE",
		"COMPOSE_PROJECT_NAME",
	):
		environment.pop(key, None)
	project = os.environ.get("PRODUCTION_PROJECT") or "cranescastle-frappe"
	if action == "delete-rehearsal":
		project = "cranescastle-frappe-rehearsal"
	if project not in ("cranescastle-frappe", "cranescastle-frappe-rehearsal"):
		raise ValueError("Use the dedicated production or rehearsal project only")
	command = [
		"docker",
		"compose",
		"--project-name",
		project,
		"--env-file",
		str(path),
		"--file",
		"deploy/compose.yaml",
	]
	if project.endswith("-rehearsal"):
		command.extend(["--file", "deploy/rehearsal.yaml"])
	if action == "backup":
		environment["BACKUP_SITE"] = values["FRAPPE_SITE"]
		config = subprocess.check_output([*command, "config", "--format", "json"], env=environment)
		subprocess.run(
			[sys.executable, "-B", "deploy/source_backup.py"], input=config, env=environment, check=True
		)
		return
	operations = {
		"logs": ["logs", "--tail", "30", "backend", "frontend", "websocket"],
		"delete-rehearsal": ["down", "--volumes", "--remove-orphans"],
		"apps": ["exec", "--no-TTY", "backend", "bench", "--site", values["FRAPPE_SITE"], "list-apps"],
		"validate": ["config", "--quiet"],
		"status": ["ps"],
		"stop": ["stop"],
		"pull": ["pull"],
		"initialize": ["run", "--rm", "initialize"],
		"restore": ["run", "--rm", "restore"],
		"start": ["up", "-d", "backend", "websocket", "frontend"],
	}
	if action not in operations:
		raise ValueError("Unknown runtime operation")
	if action in ("initialize", "start", "restore") and project != "cranescastle-frappe-rehearsal":
		raise ValueError("Initialization/start currently restricted to the isolated rehearsal project")
	if action == "restore":
		backup = Path(os.environ.get("RESTORE_BACKUP_DIR") or ".missing-backup").resolve()
		if not (backup / "manifest.json").is_file():
			raise ValueError("RESTORE_BACKUP_DIR must contain the captured backup manifest")
		environment["RESTORE_BACKUP_DIR"] = str(backup)
	subprocess.run([*command, *operations[action]], env=environment, check=True)


if __name__ == "__main__":
	try:
		main()
	except (ValueError, OSError, subprocess.CalledProcessError) as error:
		raise SystemExit(str(error)) from None
