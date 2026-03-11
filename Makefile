.PHONY: help test test-unit test-integration test-all clean install lint format

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
	pip install -r requirements-dev.txt

test-unit: ## Run unit tests only
	pytest -m "unit" -v --cov=src --cov-report=html --cov-report=term-missing

test-integration: ## Run integration tests only
	pytest -m "integration" -v

test-slow: ## Run slow tests only
	pytest -m "slow" -v

test-all: ## Run all tests
	pytest -v --cov=src --cov-report=html --cov-report=term-missing

test: ## Run quick tests (unit + integration, excluding slow)
	pytest -m "unit or integration" -v

clean: ## Clean up test artifacts
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint: ## Run linting (if you have flake8 installed)
	flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503

format: ## Format code (if you have black installed)
	black src/ tests/ --line-length=100

check: lint test ## Run all checks (lint + test)

ci: install test-all ## Full CI pipeline
