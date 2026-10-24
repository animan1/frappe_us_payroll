# Private rehearsal snapshots

After the empty-site exercise, with `PRODUCTION_ENV` and `PRODUCTION_PROJECT` selected:

```sh
make production-backup
```

Expect a private directory under `.local/backups` containing a transactionally captured
`database.sql.gz`, `site-files.tar.gz` (public/private files and original site config),
and SHA-256 `manifest.json`. Files/config are streamed directly to mode-0600 local
files in a mode-0700 directory; contents and credentials are never printed. The database
administrator credential stays inside its container and a temporary defaults file,
not process arguments. Capture the printed directory for the separate restore exercise.

This is an operator snapshot, not unattended backup automation. Source writes are
not frozen, so database/files consistency is not established for a final migration.
The archive includes the site encryption key: keep it outside Git and review evidence.
No source database grants are changed. A failed capture retains a private partial
directory without a successful manifest; do not treat it as a usable backup.

Laptop-only diagnostics use the existing development Compose context:

```sh
make migration-check-database
make migration-backup
```

These can capture `frappe-us-payroll.localhost` using the existing development DB
administrator even when the site account fails authentication. They must never target
the Droplet. The real-data restore is separately deferred by the owner; use the empty
rehearsal site's snapshot to exercise the restore mechanism first.
