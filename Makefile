.PHONY: install test lint docker-up docker-down

# Python commands
PYTHON=python
PIP=pip
PYTEST=pytest

# Docker commands
DOCKER_COMPOSE=docker-compose

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	$(PIP) install pytest pytest-asyncio pytest-mock

test-security:
	PYTHONIOENCODING="utf-8" $(PYTHON) backend/tests/test_phase9_15_security_validation.py

test-unit:
	# Run tests with dummy API keys to simulate CI environment
	GEMINI_API_KEY="dummy" XAI_API_KEY="dummy" HF_TOKEN="dummy" $(PYTHON) -m $(PYTEST) backend/tests/ -v

test: test-security test-unit

makemigrations:
	cd backend && alembic revision --autogenerate -m "Migration"

migrate:
	cd backend && alembic upgrade head

docker-up:
	$(DOCKER_COMPOSE) up -d --build

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f
