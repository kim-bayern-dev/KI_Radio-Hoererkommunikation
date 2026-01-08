.PHONY: help build start stop install app reloaddb eval

help:
	@echo "Makefile for managing the project"
	@echo "Usage:"
	@echo "  make help      - Show this help message"
	@echo "  make build     - build the docker image"
	@echo "  make start     - start the application with docker"
	@echo "  make stop      - stop the application with docker"
	@echo "  make install   - Install dependencies"
	@echo "  make app       - Run the application with python"
	@echo "  make reloaddb  - Reload the database and ingest data"
	@echo "  make eval      - Run the llm testsuite for the application"

build:
	docker compose build --pull --no-cache

start:
	docker compose up --force-recreate -d

stop:
	docker compose down -v --remove-orphans

install:
	poetry install

app:
	poetry run python src/app.py --config config-kesselbach.yaml

reloaddb:
	@echo "Deleting and reloading the database..."
	rm -rf data/sample-lancedb
	poetry run python src/db/setup.py
	@echo "Reloading live transcripts..."
	poetry run python src/ingest_transcript.py --config config-kesselbach.yaml
	@echo "Reloading website data..."
	poetry run python src/ingest_website.py --config config-kesselbach.yaml
	@echo "Database reloaded successfully."

eval:
	poetry run python src/eval.py --config eval-config.yaml


eval-docker:
	docker compose -f docker-compose-eval.yml up \
	  --build --abort-on-container-exit --exit-code-from eval \
	  --no-attach ollama
	docker compose -f docker-compose-eval.yml down -v
