SHELL := /bin/bash
.DEFAULT_GOAL := help

APP := frappe_us_payroll
SITE ?= hrms.localhost
SLIP ?=
BENCH_DIR ?= /home/frappe/frappe-bench
UV_CACHE_DIR ?= /tmp/frappe-us-payroll-uv-cache
COMPOSE_PROJECT ?= docker
HRMS_COMPOSE_FILE ?= ../hrms/docker/docker-compose.yml
COMPOSE := FRAPPE_US_PAYROLL_DIR=$(CURDIR) docker compose --project-name $(COMPOSE_PROJECT) --file $(HRMS_COMPOSE_FILE) --file compose.yaml

.PHONY: help up down restart wait health ps logs logs-tail shell apps versions link register install bench-deps migrate e2e-demo recalculate-slip enable-tests deps-lock deps unit test format format-check lint typecheck check verify reset seed


help:
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Create or start the Frappe development environment.
	$(COMPOSE) up --detach

down: ## Stop and remove the Frappe development containers.
	$(COMPOSE) down

restart: ## Restart the Frappe container after app installation or dependency changes.
	$(COMPOSE) restart frappe
	@$(MAKE) wait

wait: ## Wait up to 60 seconds for the configured Frappe site to answer.
	@for attempt in $$(seq 1 60); do \
		if curl --fail --silent http://$(SITE):8000/api/method/ping >/dev/null; then \
			echo "Frappe is ready"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "Frappe did not become ready within 60 seconds" >&2; \
	exit 1

health: ## Verify that the configured Frappe site answers HTTP requests.
	curl --fail --silent --show-error http://$(SITE):8000/api/method/ping
	@printf "\n"

ps: ## Show the development containers and their current status.
	$(COMPOSE) ps --all

logs: ## Follow the Frappe container log.
	$(COMPOSE) logs --tail 100 --follow frappe

logs-tail: ## Show recent Frappe container logs without following them.
	$(COMPOSE) logs --tail 200 frappe

shell: ## Open a shell in the Frappe bench container.
	$(COMPOSE) exec --workdir $(BENCH_DIR) frappe bash

apps: ## List apps installed on the configured Frappe site.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) list-apps

versions: ## Show the Frappe bench app versions.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench version

link: ## Link the bind-mounted working tree into the Frappe bench.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bash -c 'test ! -e apps/$(APP) || test -L apps/$(APP)'
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe ln --symbolic --force --no-target-directory /workspace/$(APP) apps/$(APP)

register: link ## Register the bind-mounted app with the bench.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe sed -i -e 's/$(APP)//g' -e '/^$$/d' sites/apps.txt
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bash -c 'printf "\n%s\n" "$(APP)" >> sites/apps.txt'

bench-deps: link ## Sync the app and its Python dependencies into the Frappe bench.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe env/bin/pip install --editable apps/$(APP)

install: register bench-deps ## Install the app package and app on the configured Frappe site (one time per site).
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) install-app $(APP)
	@$(MAKE) restart

migrate: link ## Migrate the configured site.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) migrate

e2e-demo: bench-deps ## Create a persistent $1,000 Salary Slip for manual UI review.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) execute frappe_us_payroll.development.ensure_social_security_e2e_demo

recalculate-slip: bench-deps ## Recalculate a draft Salary Slip; pass SLIP="...".
	@test -n "$(SLIP)" || (echo 'SLIP is required' >&2; exit 2)
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) execute frappe_us_payroll.development.recalculate_salary_slip --args '["$(SLIP)"]'

deps-lock: ## Resolve application and development dependencies into uv.lock.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv lock

deps: ## Install the locked application and development dependencies.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync --all-groups --frozen

unit: deps ## Run tests that do not require a Frappe site.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --frozen python -m unittest discover -s tests -p 'test_*.py'

enable-tests: ## Enable Frappe tests on the configured development site.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) set-config allow_tests true

test: bench-deps enable-tests ## Run all app tests against the configured Frappe site.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) run-tests --app $(APP)

format: deps ## Format Python source with the locked Ruff version.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --frozen ruff format .
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --frozen ruff check --fix .

format-check: deps ## Check Python formatting without changing files.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --frozen ruff format --check .

lint: deps ## Lint Python source with the locked Ruff version.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --frozen ruff check .

typecheck: deps ## Type-check Python source with the locked MyPy version.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run --frozen mypy frappe_us_payroll tests

check: format-check lint typecheck unit ## Run the local non-Frappe verification suite.

verify: check test ## Run the complete local and Frappe integration verification suite.

reset:
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) reinstall --yes \
		--admin-password Administrator \
		--mariadb-root-password 123
	$(MAKE) migrate
	$(MAKE) seed

seed:
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) execute frappe_us_payroll.development.seed