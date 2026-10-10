from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_tls_proxy_publishes_its_https_identity_on_integration_network() -> None:
	compose = (ROOT / "compose.yaml").read_text()
	nginx = (ROOT / "docker/local-https.conf").read_text()

	assert "aliases:\n          - frappe-us-payroll.localhost" in compose
	assert "name: ${LOCAL_INTEGRATION_NETWORK:-local-integrations}" in compose
	assert "listen 8445 ssl;" in nginx
	assert "host.docker.internal" not in (ROOT / "Makefile").read_text()


def test_up_creates_integration_network() -> None:
	result = subprocess.run(
		["make", "--dry-run", "up"],
		cwd=ROOT,
		check=True,
		capture_output=True,
		text=True,
	)

	assert 'docker network inspect "local-integrations"' in result.stdout
	assert 'docker network create "local-integrations"' in result.stdout
