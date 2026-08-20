SHELL := /bin/bash
.DEFAULT_GOAL := help

APP := frappe_us_payroll
SITE ?= hrms.localhost
BENCH_DIR ?= /home/frappe/frappe-bench
RUFF_VERSION ?= 0.12.11
MYPY_VERSION ?= 1.17.1
UV_CACHE_DIR ?= /tmp/frappe-us-payroll-uv-cache
COMPOSE_PROJECT ?= docker
HRMS_COMPOSE_FILE ?= ../hrms/docker/docker-compose.yml
COMPOSE := FRAPPE_US_PAYROLL_DIR=$(CURDIR) docker compose --project-name $(COMPOSE_PROJECT) --file $(HRMS_COMPOSE_FILE) --file compose.yaml

.PHONY: help up down restart wait health ps logs logs-tail shell apps versions link register install migrate enable-tests unit test format format-check lint typecheck check verify

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

install: register ## Install the app package and app on the configured Frappe site (one time per site).
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe env/bin/pip install --editable apps/$(APP)
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) install-app $(APP)
	@$(MAKE) restart

migrate: link ## Migrate the configured site.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) migrate

unit: ## Run tests that do not require a Frappe site.
	python3 -m unittest discover -s tests -p 'test_*.py'

enable-tests: ## Enable Frappe tests on the configured development site.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) set-config allow_tests true

test: link enable-tests ## Run all app tests against the configured Frappe site.
	$(COMPOSE) exec --no-TTY --workdir $(BENCH_DIR) frappe bench --site $(SITE) run-tests --app $(APP)

format: ## Format Python source with the pinned Ruff version.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from ruff==$(RUFF_VERSION) ruff format .
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from ruff==$(RUFF_VERSION) ruff check --fix .

format-check: ## Check Python formatting without changing files.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from ruff==$(RUFF_VERSION) ruff format --check .

lint: ## Lint Python source with the pinned Ruff version.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from ruff==$(RUFF_VERSION) ruff check .

typecheck: ## Type-check Python source with the pinned MyPy version.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from mypy==$(MYPY_VERSION) mypy frappe_us_payroll tests

check: format-check lint typecheck unit ## Run the local non-Frappe verification suite.

verify: check test ## Run the complete local and Frappe integration verification suite.
