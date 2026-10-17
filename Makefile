.PHONY: install format lint test pre-pr run

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
