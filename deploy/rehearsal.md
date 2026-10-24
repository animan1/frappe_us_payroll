# Empty-site operator exercise

Requires Docker and the custom image built by `make production-build`. This uses
the same application services as production, with an isolated project and application
network. Only nginx joins an edge network to publish its loopback port. Application
outbound connections are blocked; workers/scheduler stay off to avoid external effects.

```sh
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

Expect the login page at `http://localhost:18081/login`, a pong response and all four
installed apps. The generated administrator password is in the private env file;
never paste it into a PR or log. The generator retains existing inputs unchanged.
Initialization refuses existing sites; initialization/start refuse the production
project. This tests runtime behavior, not parity with the laptop's data.

The runtime uses Frappe's official production Gunicorn entrypoint and a tenant-local
MariaDB client config for the source-compatible 10.8 server. The DB connection is
unencrypted inside the private Docker network; no database port is published. Never
reuse that client config for a remote DB. Caddy supplies public HTTPS separately.

```sh
make production-stop
```

Stop preserves all data. For an intentional clean slate, the following command deletes
only the fixed rehearsal project and its volumes, regardless of any project override:

```sh
make production-rehearsal-delete
```
