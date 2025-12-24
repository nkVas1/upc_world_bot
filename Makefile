# Makefile for UPC World Bot

.PHONY: help install dev format lint test coverage clean docker docker-logs docker-shell db-migrate db-reset run

help:
	@echo "UPC World Bot - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Install dev dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format        - Format code with black"
	@echo "  make lint          - Run linters (flake8, mypy)"
	@echo "  make test          - Run tests"
	@echo "  make coverage      - Run tests with coverage report"
	@echo ""
	@echo "Running:"
	@echo "  make run           - Run bot locally"
	@echo "  make docker        - Run with Docker Compose"
	@echo "  make docker-logs   - Show Docker logs"
	@echo "  make docker-shell  - Open shell in bot container"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate    - Apply database migrations"
	@echo "  make db-reset      - Reset database"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Clean up temporary files"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black flake8 mypy

format:
	black bot/

lint:
	flake8 bot/ --max-line-length=100
	mypy bot/ --ignore-missing-imports || true

test:
	pytest

coverage:
	pytest --cov=bot --cov-report=html --cov-report=term-missing

docker:
	docker-compose up -d

docker-logs:
	docker-compose logs -f bot

docker-shell:
	docker-compose exec bot /bin/bash

db-migrate:
	docker-compose exec bot alembic upgrade head

db-reset:
	docker-compose down -v
	docker-compose up -d

run:
	python -m bot.main

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
