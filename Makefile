PROFILE ?=

COMPOSE_DEV = docker compose $(if $(PROFILE),--profile $(PROFILE)) \
	--env-file ./configs/.env.dev \
	--env-file ./configs/overrides/.env.dev \
	-p service_dev

ENV_VARS_DEV = ENV_FILE=./configs/.env.dev ENV_FILE_OVERRIDE=./configs/overrides/.env.dev

COMPOSE_TEST = docker compose $(if $(PROFILE),--profile $(PROFILE)) \
	--env-file ./configs/.env.test \
	--env-file ./configs/overrides/.env.test \
	-p service_test

ENV_VARS_TEST = ENV_FILE=./configs/.env.test ENV_FILE_OVERRIDE=./configs/overrides/.env.test

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -type f -delete

test-stack-up:
	$(ENV_VARS_TEST) $(COMPOSE_TEST) up -d

test-stack-down:
	$(ENV_VARS_TEST) $(COMPOSE_TEST) down

test-stack-logs:
	$(ENV_VARS_TEST) $(COMPOSE_TEST) logs

test:
	uv run coverage run -m pytest --envfile .env.test
	uv run coverage report

test-stack-up-and-run: test-stack-up
	uv run coverage run -m pytest
	uv run coverage report

dev-stack-up:
	$(ENV_VARS_DEV) $(COMPOSE_DEV) up -d
	sleep 5
	alembic upgrade head

dev-stack-down:
	$(ENV_VARS_DEV) $(COMPOSE_DEV) down

dev-stack-logs:
	$(ENV_VARS_DEV) $(COMPOSE_DEV) logs

format:
	ruff check
	ruff format

.PHONY: check run clean test
