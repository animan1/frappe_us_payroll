# Independent production runtime (preparation)

This is a tenant-owned Compose project, separate from the laptop development bench
and shared Caddy. The executable rehearsal uses the production services, a separate
Compose project and blocked outbound networking. Production activation remains gated
until the real-data restore and source customizations are accepted. Never use the
development bench image or default passwords.

Create a private mode-0600 env file outside Git and set `PRODUCTION_ENV` to its path.
Required inputs are `FRAPPE_IMAGE`, `MARIADB_IMAGE`, `REDIS_IMAGE` (all digest-pinned;
local immutable image IDs are also accepted for rehearsal),
`FRAPPE_SITE` (the restored site's name), and a newly generated
`MARIADB_ROOT_PASSWORD` of at least 24 random letters/digits/underscores/hyphens.
This alphabet avoids Compose interpolation of credential characters. Use plain unquoted env values;
do not paste credentials into shell arguments or review evidence.
`FRAPPE_ADMIN_PASSWORD` follows the same private random-password requirement.

```sh
make production-test
make production-validate
make production-pull
make production-status
```

Validation prints no expanded configuration. Pull downloads images without starting
services. Status must not affect development containers. `make production-stop` stops
only the selected independent project and preserves volumes.
Only the frontend publishes a host port: `127.0.0.1:18081`. Caddy owns public TLS.
Database, Redis, backend and Socket.IO stay within this tenant's network.

## Empty-site rehearsal

Run from this checkout on the operator computer, with Docker running. The build
fetches exact source commits into ignored `.local/production-build` and uses a pinned
revision of Frappe's official production image recipe. It does not read the laptop
site or copy its volumes. Uncommitted upstream app changes are intentionally not
included; this image must not be claimed to reproduce those changes.

```sh
make production-build
make production-rehearsal-inputs
export PRODUCTION_ENV=.local/rehearsal.env
export PRODUCTION_PROJECT=cranescastle-frappe-rehearsal
make production-validate
make production-initialize
make production-start
make production-smoke
make production-apps
make production-status
```

The private input generator preserves existing inputs rather than rotating passwords.
It uses cached MariaDB/Redis images by digest and the newly built application image ID.
Initialization refuses an existing site. Both initialization and start currently
refuse the production project. The rehearsal override changes only network isolation:
application outbound traffic must be blocked because restored integrations may contain live settings.
Only the nginx frontend joins an edge network to expose its loopback port; application
backend, Socket.IO, database and Redis remain on the isolated network.
Workers and scheduler remain off. Open `http://localhost:18081/login` for a direct
origin check; shared Caddy supplies the final hostname and TLS separately.

For a disposable backup/restore exercise, capture only the empty rehearsal site:

```sh
make production-backup
```

Set `RESTORE_BACKUP_DIR` to the directory printed by that command, then:

```sh
make production-stop
make production-restore
make production-start
make production-smoke
```

Restore verifies archive checksums before database changes and requires the empty-site
marker. It retains destination database credentials, restores source encryption keys
and public/private files, migrates, and removes that marker. It cannot be repeated
over a destination receiving new edits. To deliberately delete the isolated rehearsal
containers and all their data (the production project can never be selected by this target):

```sh
make production-rehearsal-delete
```

The MariaDB CLI configuration disables client TLS only for the tenant-local database
connection, matching the source MariaDB 10.8 server. No database port is published.
This configuration must not be reused for a remote database. Shared Caddy still owns
public HTTPS. The runtime uses the official production Gunicorn start script so its
working directory, logger paths and preload behavior match the upstream deployment.
An interrupted restore requires administrator inspection; no automatic retry occurs.

## Restore rehearsal contract

Inspect the existing development source without printing configuration or records:

```sh
make migration-inspect
```

This lists source commit IDs, dirty app paths, and backup filenames/sizes. It never
starts or recreates containers. Stop if app changes are not represented in the planned
image: database/file backups do not include uncommitted Python code. Preserve those
changes privately and reconcile them with the owner before claiming visual/functional
parity. Never reset the source apps to make this check pass.

Restore from a Frappe backup, not by copying live Docker volumes. Include the matching
database dump, public/private file archives, and securely retained site encryption key.
Use the exact source app revisions and source-compatible database/runtime images first.
Keep backups private and verify archive checksums before and after transfer. Record
their creation time so a stale backup is never mistaken for the final migration copy.

Restore into a fresh isolated project with disposable destination volumes; preserve
the laptop source. Neither the worker nor scheduler starts without the `live` profile.
That profile is for the eventual approved production activation, never rehearsal.
Also disable application outbound email and integrations before serving restored data;
profiles alone cannot prevent requests from invoking external services.

Check login, existing customization, assets, attachments and representative records
without submitting or recalculating payroll. A successful restore is the backup test.
For final migration, freeze source writes, create a fresh backup and repeat the tested
restore procedure; then designate one writable authority. Do not blindly overwrite a
destination that has received newer edits.

The source selected by the owner is `frappe-us-payroll.localhost`, currently accessed
on port 8445; production is `frappe.cranescastlebeer.com`. The selected source currently
fails site-account database authentication while the health ping succeeds. Read-only
administrator inspection confirmed that its database still exists. The development
`migration-check-database` and `migration-backup` targets can check it and create a
private rehearsal snapshot using existing development DB administrator access,
without altering grants or printing credentials. These are not production backup
automation: the source is not write-frozen, so the snapshot is not a final migration
backup. Never use them against the Droplet.

The initial inventory found no backups in that site directory and uncommitted Employee
changes in ERPNext plus Salary Register changes in HRMS. Their contents were not copied
into this repository. The owner deferred real-data restore; the exercised round trip
uses only an empty disposable site's backup. Keep real-data and customization acceptance
separate from that plumbing test.
