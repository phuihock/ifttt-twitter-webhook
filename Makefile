# Makefile for IFTTT Twitter Webhook

# Variables
PYTHON := python3
PIP := pip3
APP := src/main.py
TESTS := tests/

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  run         - Run the application"
	@echo "  test        - Run tests"
	@echo "  clean       - Clean up temporary files"
	@echo "  lint        - Run code linter"
	@echo "  format      - Format code with black"
	@echo "  docker      - Build Docker image"
	@echo "  migrate     - Apply database migrations (generic framework)"
	@echo "  help        - Show this help message"

# Install dependencies
.PHONY: install
install:
	$(PIP) install -r requirements/base.txt

# Run the application
.PHONY: run
run:
	$(PYTHON) $(APP)

# Run tests
.PHONY: test
test:
	$(PYTHON) -m pytest $(TESTS) -v

# Clean up temporary files
.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f *.log
	rm -f data/*.db

# Run code linter
.PHONY: lint
lint:
	$(PYTHON) -m flake8 src/ tests/

# Format code with black
.PHONY: format
format:
	$(PYTHON) -m black src/ tests/

# Build Docker image
.PHONY: docker
docker:
	docker build -t ghcr.io/phuihock/ifttt-twitter-webhook:main .

# Start application with Docker Compose
.PHONY: compose-up
compose-up:
	docker-compose up -d

# Stop application with Docker Compose
.PHONY: compose-down
compose-down:
	docker-compose down

# Install development dependencies
.PHONY: dev-install
dev-install:
	$(PIP) install -r requirements/base.txt
	$(PIP) install -r requirements/dev.txt

# Run the application in development mode
.PHONY: dev
dev:
	$(PYTHON) $(APP)

# Apply database migrations
.PHONY: migrate
migrate:
	./migrate.sh

# Install dependencies including development dependencies
.PHONY: install-all
install-all:
	$(PIP) install -r requirements/base.txt
	$(PIP) install -r requirements/dev.txt