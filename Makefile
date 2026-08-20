SHELL := /bin/bash
.DEFAULT_GOAL := help

APP := frappe_us_payroll
SITE ?= hrms.localhost
FRAPPE_CONTAINER ?= docker-frappe-1
MARIADB_CONTAINER ?= docker-mariadb-1
REDIS_CONTAINER ?= docker-redis-1
BENCH_DIR ?= /home/frappe/frappe-bench
RUFF_VERSION ?= 0.12.11
UV_CACHE_DIR ?= /tmp/frappe-us-payroll-uv-cache

.PHONY: help up down restart wait health ps logs logs-tail shell apps versions sync register install migrate enable-tests unit test format format-check lint check verify

help:
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start the existing Frappe development containers without recreating them.
	docker start $(MARIADB_CONTAINER) $(REDIS_CONTAINER) $(FRAPPE_CONTAINER)

down: ## Stop the existing Frappe development containers.
	docker stop $(FRAPPE_CONTAINER) $(REDIS_CONTAINER) $(MARIADB_CONTAINER)

restart: ## Restart the Frappe container after app installation or dependency changes.
	docker restart $(FRAPPE_CONTAINER)
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
	docker ps -a --filter name=$(FRAPPE_CONTAINER) --filter name=$(MARIADB_CONTAINER) --filter name=$(REDIS_CONTAINER)

logs: ## Follow the Frappe container log.
	docker logs --tail 100 --follow $(FRAPPE_CONTAINER)

logs-tail: ## Show recent Frappe container logs without following them.
	docker logs --tail 200 $(FRAPPE_CONTAINER)

shell: ## Open a shell in the existing Frappe bench container.
	docker exec --interactive --tty --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) bash

apps: ## List apps installed on the configured Frappe site.
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) bench --site $(SITE) list-apps

versions: ## Show the Frappe bench app versions.
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) bench version

sync: ## Copy the working tree's app files into the existing bench container.
	docker exec $(FRAPPE_CONTAINER) mkdir -p $(BENCH_DIR)/apps/$(APP)/$(APP)
	docker cp pyproject.toml $(FRAPPE_CONTAINER):$(BENCH_DIR)/apps/$(APP)/pyproject.toml
	docker cp README.md $(FRAPPE_CONTAINER):$(BENCH_DIR)/apps/$(APP)/README.md
	docker cp MANIFEST.in $(FRAPPE_CONTAINER):$(BENCH_DIR)/apps/$(APP)/MANIFEST.in
	docker cp $(APP)/. $(FRAPPE_CONTAINER):$(BENCH_DIR)/apps/$(APP)/$(APP)

register: sync ## Register the synchronized app with the existing bench.
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) sed -i -e 's/$(APP)//g' -e '/^$$/d' sites/apps.txt
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) bash -c 'printf "\n%s\n" "$(APP)" >> sites/apps.txt'

install: register ## Install the app package and app on the configured Frappe site (one time per site).
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) env/bin/pip install --editable apps/$(APP)
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) bench --site $(SITE) install-app $(APP)
	@$(MAKE) restart

migrate: sync ## Synchronize the app and migrate the configured site.
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) bench --site $(SITE) migrate

unit: ## Run tests that do not require a Frappe site.
	python3 -m unittest discover -s tests -p 'test_*.py'

enable-tests: ## Enable Frappe tests on the configured development site.
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) bench --site $(SITE) set-config allow_tests true

test: sync enable-tests ## Run all app tests against the configured Frappe site.
	docker exec --workdir $(BENCH_DIR) $(FRAPPE_CONTAINER) bench --site $(SITE) run-tests --app $(APP)

format: ## Format Python source with the pinned Ruff version.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from ruff==$(RUFF_VERSION) ruff format .
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from ruff==$(RUFF_VERSION) ruff check --fix .

format-check: ## Check Python formatting without changing files.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from ruff==$(RUFF_VERSION) ruff format --check .

lint: ## Lint Python source with the pinned Ruff version.
	UV_CACHE_DIR=$(UV_CACHE_DIR) uvx --from ruff==$(RUFF_VERSION) ruff check .

check: format-check lint unit ## Run the local non-Frappe verification suite.

verify: check test ## Run the complete local and Frappe integration verification suite.
