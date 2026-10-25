# Needs docker compose and a POSIX shell (Git Bash on Windows).
# `make test` runs on the host: pip install -r requirements-dev.txt first.
PYTHON ?= python
COMPOSE = docker compose
RUNS ?= 1
TASKS ?=
USERS ?= 1 5 10 20
LABEL ?= real

.PHONY: build up down logs test eval load-test clean

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --wait

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

test:
	$(PYTHON) -m pytest tests -q

eval:
	$(COMPOSE) --profile tools run --rm --no-deps eval python eval/run_eval.py --runs $(RUNS) $(if $(TASKS),--tasks $(TASKS))

# for an infra-only run: FAKE_LLM=1 LLM_MAX_RPM=0 make up, then make load-test LABEL=fake
# each level runs for $DURATION (default 4m)
load-test:
	bash loadtest/run_levels.sh $(LABEL) $(USERS)
	$(PYTHON) loadtest/summarize.py

# stops everything, deletes the volumes, and removes sandbox containers left by a crash
clean:
	$(COMPOSE) --profile tools down -v --remove-orphans
	docker ps -aq --filter label=app=pipeline-sandbox | xargs -r docker rm -f
	docker volume ls -q --filter label=app=pipeline-sandbox | xargs -r docker volume rm
