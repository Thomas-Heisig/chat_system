.PHONY: help install install-dev install-all run test lint format clean docker-build docker-up docker-down

help:
	@echo "Chat System - Available Commands"
	@echo "================================="
	@echo "install          - Install basic dependencies"
	@echo "install-dev      - Install with dev dependencies"
	@echo "install-all      - Install all optional dependencies"
	@echo "run              - Run the application"
	@echo "test             - Run tests"
	@echo "test-cov         - Run tests with coverage"
	@echo "lint             - Run linters (flake8)"
	@echo "format           - Format code with black and isort"
	@echo "format-check     - Check code formatting without changes"
	@echo "clean            - Remove temporary files"
	@echo "docker-build     - Build Docker image"
	@echo "docker-up        - Start services with docker-compose"
	@echo "docker-down      - Stop docker-compose services"
	@echo "docker-logs      - View docker-compose logs"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"

install-all:
	pip install -e ".[all]"

run:
	python main.py

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

lint:
	flake8 .

format:
	black .
	isort .

format-check:
	black --check .
	isort --check-only .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.bak" -delete
	find . -type f -name "*:Zone.Identifier" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build:
	docker build -t chat-system:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f
