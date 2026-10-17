IMAGE = ghcr.io/tahardi/health-value-dashboard

.PHONY: install format lint test pre-pr run data reference docker-build docker-run-dev docker-run

install:
	uv sync

format:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff format --check .
	uv run ruff check .

test:
	uv run pytest

pre-pr: format lint test

run:
	uv run shiny run \
		app.app:app \
		--reload \
		--port 8000

data:
	uv run python -m scripts.generate_data

reference:
	docker run \
		--rm \
		--user $(shell id -u):$(shell id -g) \
		-v $(PWD):/work \
		-w /work \
		rocker/r-ver:4.4.1 \
		Rscript reference/compute.R

docker-build:
	docker build \
		-t health-value-dashboard:dev \
		.

docker-run-dev:
	mkdir -p .hvd-data
	docker run \
		--rm \
		--user $(shell id -u):$(shell id -g) \
		-p 8000:8000 \
		-v $(PWD)/.hvd-data:/data \
		health-value-dashboard:dev

docker-run:
	mkdir -p .hvd-data
	docker run \
		--rm \
		--pull always \
		--user $(shell id -u):$(shell id -g) \
		-p 8000:8000 \
		-v $(PWD)/.hvd-data:/data \
		$(IMAGE):latest
