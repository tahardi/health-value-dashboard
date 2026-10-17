.PHONY: install format lint test pre-pr run data reference

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
		app/app.py \
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
