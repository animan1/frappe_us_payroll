# Independent production runtime (preparation)

For a data-free running site, follow the [empty-site exercise](rehearsal.md).

Build the custom image without reading any site data, then generate private rehearsal
inputs from its immutable image identity and cached database/Redis digests:

```sh
make production-build
make production-rehearsal-inputs
```

The build uses exact app commits and a pinned revision of Frappe's official production
Docker recipe. Its full log stays in ignored `.local/production-build/build.log`.
Uncommitted source changes are not included; reconcile them before a real-data migration.
Site initialization and backup/restore are separate dependent slices.

This is a tenant-owned Compose project, separate from the laptop development bench
and shared Caddy. Follow [empty-site rehearsal](rehearsal.md), [backup](backup.md),
then [restore](restore.md). Production activation remains gated until the real-data
restore and source customizations are accepted. Never use the development bench image
or default passwords.

Create a private mode-0600 env file outside Git and set `PRODUCTION_ENV` to its path.
Required inputs are `FRAPPE_IMAGE`, `MARIADB_IMAGE`, `REDIS_IMAGE` (all digest-pinned),
`FRAPPE_SITE` (the restored site's name), `FRAPPE_ADMIN_PASSWORD`, and a newly generated
`MARIADB_ROOT_PASSWORD` of at least 24 random letters/digits/underscores/hyphens.
This alphabet avoids Compose interpolation of credential characters. Use plain unquoted env values;
do not paste credentials into shell arguments or review evidence.

```sh
make production-test
make production-validate
make production-pull
make production-status
```

Validation prints no expanded configuration. Pull downloads images without starting
services. Status must not affect development containers. `make production-stop` stops
only the selected project and preserves volumes. The separately named
`production-rehearsal-delete` deletes only the isolated rehearsal and all its data.
Only the frontend publishes a host port: `127.0.0.1:18081`. Caddy owns public TLS.
Database, Redis, backend and Socket.IO stay within this tenant's network.

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
fails database authentication in `make apps SITE=frappe-us-payroll.localhost` while
the health ping succeeds. A known-good existing backup can unblock the restore
rehearsal independently of that live connection. No backup was selected or restored
by this preparation slice. The initial inventory found no backups in the selected
site directory and uncommitted Employee changes in ERPNext plus Salary Register
changes in HRMS. Their contents were not copied into this repository. Restoring a
known-good separately stored backup is preferred to repairing source database grants.
