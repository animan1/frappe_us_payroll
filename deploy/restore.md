# Isolated backup restore exercise

Prerequisites: complete the empty-site exercise and its backup. Retain the same private
`PRODUCTION_ENV` and select `PRODUCTION_PROJECT=cranescastle-frappe-rehearsal`. Set
`RESTORE_BACKUP_DIR` to the private directory printed by `make production-backup`.

```sh
make production-stop
make production-restore
make production-start
make production-smoke
make production-apps
```

Expect checksum verification, database restore, file extraction and schema migration,
then successful login, built-asset, ping and realtime checks, and all four apps in the database-backed list.
Open `http://localhost:18081/login`. The existing generated administrator password is
retained as the destination administrator password; it stays in the private env file.

The snapshot format is `database.sql.gz`, `site-files.tar.gz` and its `manifest.json`
from the preceding capture step. Public/private files and original encryption keys
are restored; destination database connection credentials are retained. No SQL, file
contents or key values are printed. Rehearsal networking blocks application outbound
traffic; workers and scheduler remain off. Root is used only by the one-off restore
container to read the private mounted archive; migration runs as the application user.

Restore refuses an existing destination unless it still has the fresh-empty marker,
and removes that marker after success. Repeating the restore must fail before database
changes. Checksum mismatch and unsafe archive members also stop before database changes.
No automatic retry is performed after an interrupted restore: inspect the destination
and failure before deciding whether to retry or delete the disposable rehearsal.

```sh
make production-restore
```

After a successful restore, expect refusal: `destination is not a fresh empty rehearsal
site`. This tests the overwrite guard. It is not an instruction to bypass it.

The exercised round trip uses an empty disposable site. Restoring the laptop data and
accepting customizations are deferred by the owner; this exercise does not establish
payroll correctness or production data parity. A final migration needs a write freeze,
a fresh consistent backup and a single agreed writable authority. Keep the laptop
authoritative until that separately approved transition. Do not change DNS here.
