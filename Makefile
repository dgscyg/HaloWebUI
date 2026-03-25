
ifneq ($(shell which docker-compose 2>/dev/null),)
    DOCKER_COMPOSE := docker-compose
else
    DOCKER_COMPOSE := docker compose
endif

NVM_INIT := source /home/dragon/.nvm/nvm.sh && nvm use 22 >/dev/null
PROJECT_ROOT := /data/other/HaloWebUI
RUN_LOCAL := $(NVM_INIT) && cd $(PROJECT_ROOT)
.PHONY: install remove start startAndBuild stop update \
	local-setup build build-full build-debug check test test-frontend validate preview

install:
	$(DOCKER_COMPOSE) up -d

remove:
	@echo "Warning: This will remove all containers and volumes, including persistent data."
	@$(DOCKER_COMPOSE) down -v

start:
	$(DOCKER_COMPOSE) start
startAndBuild: 
	$(DOCKER_COMPOSE) up -d --build

stop:
	$(DOCKER_COMPOSE) stop

update:
	@git pull
	$(DOCKER_COMPOSE) down
	# Make sure the ollama-webui container is stopped before rebuilding
	@docker stop open-webui || true
	$(DOCKER_COMPOSE) up --build -d
	$(DOCKER_COMPOSE) start

local-setup:
	$(RUN_LOCAL) && uv sync --frozen

build:
	$(RUN_LOCAL) && npm run build

build-full:
	$(RUN_LOCAL) && npm run build:full

build-debug:
	$(RUN_LOCAL) && npm run build:debug

check:
	$(RUN_LOCAL) && npm run check

test:
	$(RUN_LOCAL) && npx vitest run && cd $(PROJECT_ROOT)/backend && ../.venv/bin/python -m pytest open_webui/test/unit/test_mcp.py -q

test-frontend:
	$(RUN_LOCAL) && npx vitest run

preview:
	$(RUN_LOCAL) && npm run preview

validate: test
	$(RUN_LOCAL) && npm run build
