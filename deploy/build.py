"""Build a data-free production image from captured source commits and upstream Docker tooling."""

import json
import subprocess
from pathlib import Path

ROOT = Path(".local/production-build").resolve()
LOCK = {
	"frappe_docker": ("frappe/frappe_docker", "ce862c7b8113ac0c6b6b83becde126c980ef2d0b"),
	"frappe": ("frappe/frappe", "dd3dd53ef717aec5b13683271b2020fa0ea49f0c"),
	"erpnext": ("frappe/erpnext", "1f839061899c019b9a326b960fc5d10b4b34c761"),
	"hrms": ("frappe/hrms", "03c2265cb6cd67b0e46417a35fd0452c49fe03e8"),
	"frappe_us_payroll": ("animan1/frappe_us_payroll", "b2ef39f9647ded9b5bc612cbcc12da170fc014da"),
}


def run(*args):
	if args[:2] == ("docker", "build"):
		log = ROOT / "build.log"
		print("Building; full output: " + str(log), flush=True)
		with log.open("w") as output:
			result = subprocess.run(args, stdout=output, stderr=subprocess.STDOUT)
		if result.returncode:
			print("\n".join(log.read_text().splitlines()[-65:]))
			raise SystemExit(result.returncode)
		return
	subprocess.run(args, check=True)


def main():
	ROOT.mkdir(parents=True, exist_ok=True)
	upstream = ROOT / "frappe_docker"
	for name, (repo, revision) in LOCK.items():
		path = upstream if name == "frappe_docker" else upstream / "sources" / name
		if not (path / ".git").exists():
			path.mkdir(parents=True, exist_ok=True)
			run("git", "init", str(path))
			run("git", "-C", str(path), "remote", "add", "origin", "https://github.com/" + repo + ".git")
		run("git", "-C", str(path), "fetch", "--depth=1", "origin", revision)
		run("git", "-C", str(path), "checkout", "-B", "migration-locked", revision)
	# Use the official production recipe and entrypoints, supplying local exact-commit
	# app repositories instead of allowing bench to follow moving upstream branches.
	recipe = (upstream / "images/custom/Containerfile").read_text()
	marker = "USER frappe\n\nARG FRAPPE_BRANCH"
	if recipe.count(marker) != 1:
		raise ValueError("Upstream build layout changed; review before adapting")
	recipe = recipe.replace(marker, "COPY --chown=frappe:0 sources /opt/sources\n\n" + marker)
	recipe = recipe.replace("    --verbose \\\n", "")
	dockerfile = upstream / "Migration.Containerfile"
	dockerfile.write_text(recipe)
	apps = ROOT / "apps.json"
	apps.write_text(
		json.dumps(
			[
				{"url": "file:///opt/sources/" + name, "branch": "migration-locked"}
				for name in ("erpnext", "hrms", "frappe_us_payroll")
			]
		)
	)
	# Explicit path context excludes source sites, credentials, volumes and backups.
	run(
		"docker",
		"build",
		"--file",
		str(dockerfile),
		"--tag",
		"cranescastle-frappe:rehearsal",
		"--build-arg",
		"FRAPPE_BRANCH=migration-locked",
		"--build-arg",
		"FRAPPE_PATH=file:///opt/sources/frappe",
		"--secret",
		"id=apps_json,src=" + str(apps),
		str(upstream),
	)
	print("Built data-free pinned-source rehearsal image; source dirty changes are NOT included.")
	print("Do not use as a source-equivalent migration release until those changes are reconciled.")


if __name__ == "__main__":
	main()
