# ==============================================================================
# Sanad Build Orchestration & Operational Automation Makefile
# ==============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help up down restart logs ps clean test lint typecheck eval loadtest audit seed keys-dev

help:
	@echo "Sanad Platform Build Targets:"
	@echo "  make up         - Start all services (PostgreSQL, Redis, MinIO, API, Worker, Web)"
	@echo "  make down       - Stop and remove all service containers"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - Tail structured service logs"
	@echo "  make ps         - Show container service status"
	@echo "  make test       - Run all test suites (unit, crypto, threats, integration)"
	@echo "  make lint       - Run static code linters on backend and frontend"
	@echo "  make typecheck  - Verify static type safety (mypy / tsc)"
	@echo "  make eval       - Execute Road B synthetic evaluation harness & generate reports"
	@echo "  make loadtest   - Execute latency and throughput benchmarks (k6/locust)"
	@echo "  make audit      - Run dependency security audit and secret leak scanning"
	@echo "  make seed       - Seed database with demo institutions and signed credentials"
	@echo "  make keys-dev   - Generate local development cryptographic key pairs"
	@echo "  make clean      - Clean temporary artifacts and cache files"

# ------------------------------------------------------------------------------
# Service Lifecycle
# ------------------------------------------------------------------------------
up:
	docker compose up -d --build

down:
	docker compose down --remove-orphans

restart:
	docker compose restart

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

# ------------------------------------------------------------------------------
# Cryptographic Keys & Seeding
# ------------------------------------------------------------------------------
keys-dev:
	@echo "Generating local development keys (ignored by git)..."
	docker compose run --rm api python -m tools.generate_dev_keys || python tools/generate_dev_keys.py

seed:
	@echo "Seeding verified demo institutions and signed certificates..."
	docker compose exec api python -m tools.seed_database || python tools/seed_database.py

# ------------------------------------------------------------------------------
# Quality & Verification Gates
# ------------------------------------------------------------------------------
test:
	@echo "Executing complete test suite (Unit, Cryptography, Threats, Integration)..."
	docker compose run --rm api pytest -v backend/tests

lint:
	@echo "Running ruff and eslint..."
	docker compose run --rm api ruff check backend/app backend/tests
	npm --prefix frontend run lint

typecheck:
	@echo "Running backend and frontend static type checkers..."
	docker compose run --rm api mypy backend/app
	npm --prefix frontend run type-check

eval:
	@echo "Running Road B synthetic forensic and OCR evaluation harness..."
	docker compose run --rm worker python -m eval.run_eval --dataset eval/manifest.json --output eval/results/

loadtest:
	@echo "Running load testing benchmarks..."
	docker compose run --rm api python -m tests.load.run_benchmarks

audit:
	@echo "Auditing dependencies and scanning for secrets..."
	docker compose run --rm api pip-audit
	npm --prefix frontend audit
	@which gitleaks > /dev/null 2>&1 && gitleaks detect --source . -v || echo "gitleaks not installed; skipping local check"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache
