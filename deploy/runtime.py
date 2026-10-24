"""Fail closed before starting the independent production Compose project."""
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


def configuration(path):
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError('Production env file must have mode 0600')
    values = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        if key in values:
            raise ValueError('Duplicate configuration key: ' + key)
        values[key] = value
    for key in ('FRAPPE_IMAGE', 'MARIADB_IMAGE', 'REDIS_IMAGE'):
        if not re.fullmatch(r'[a-z0-9./:_-]+@sha256:[0-9a-f]{64}', values.get(key, '')):
            raise ValueError(key + ' must identify an immutable image digest')
    if not re.fullmatch(r'[a-z0-9.-]+', values.get('FRAPPE_SITE', '')):
        raise ValueError('Invalid restored site name')
    if not re.fullmatch(r'[A-Za-z0-9_-]{24,}', values.get('MARIADB_ROOT_PASSWORD', '')):
        raise ValueError('Supply a private random database password: 24+ letters/digits/_/-')
    return values


def main():
    action = sys.argv[1]
    path = Path(os.environ.get('PRODUCTION_ENV') or '.local/production.env').resolve()
    configuration(path)
    # Prevent ambient workstation variables from overriding the reviewed private inputs.
    environment = dict(os.environ)
    for key in ('FRAPPE_IMAGE', 'MARIADB_IMAGE', 'REDIS_IMAGE', 'FRAPPE_SITE', 'MARIADB_ROOT_PASSWORD',
                'COMPOSE_PROFILES', 'COMPOSE_FILE', 'COMPOSE_PROJECT_NAME'):
        environment.pop(key, None)
    command = ['docker', 'compose', '--project-name', 'cranescastle-frappe',
               '--env-file', str(path), '--file', 'deploy/compose.yaml']
    operations = {'validate': ['config', '--quiet'], 'status': ['ps'],
                  'stop': ['stop'], 'pull': ['pull']}
    if action not in operations:
        raise ValueError('Runtime activation is unavailable until configuration/restore rehearsal passes')
    subprocess.run([*command, *operations[action]], env=environment, check=True)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
