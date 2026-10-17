IMAGE = ghcr.io/tahardi/health-value-dashboard
IMAGE_LABEL = org.opencontainers.image.source=https://github.com/tahardi/health-value-dashboard

.DEFAULT_GOAL := pre-pr

.PHONY: pre-pr
pre-pr: install data reference format lint test docker-build

.PHONY: install
install:
	uv sync

.PHONY: format
format:
	uv run ruff format .
	uv run ruff check --fix .

.PHONY: lint
lint:
	uv run ruff format --check .
	uv run ruff check .

.PHONY: test
test:
	uv run pytest

.PHONY: run
run:
	uv run shiny run \
		app.app:app \
		--reload \
		--port 8000

.PHONY: screenshots
screenshots:
	uv run python -m scripts.screenshots

.PHONY: data
data:
	uv run python -m scripts.generate_data

.PHONY: reference
reference:
	docker run \
		--rm \
		--user $(shell id -u):$(shell id -g) \
		-v $(PWD):/work \
		-w /work \
		rocker/r-ver:4.4.1 \
		Rscript reference/compute.R

.PHONY: docker-build
docker-build:
	docker build \
		-t health-value-dashboard:dev \
		.

# Runs the most recent local build, made by docker-build.
.PHONY: docker-run-local
docker-run-local:
	mkdir -p .hvd-data
	docker run \
		--rm \
		--user $(shell id -u):$(shell id -g) \
		-p 8000:8000 \
		-v $(PWD)/.hvd-data:/data \
		health-value-dashboard:dev

# Runs the most recent image published to the GitHub container registry.
.PHONY: docker-run-registry
docker-run-registry:
	mkdir -p .hvd-data
	docker run \
		--rm \
		--pull always \
		--user $(shell id -u):$(shell id -g) \
		-p 8000:8000 \
		-v $(PWD)/.hvd-data:/data \
		$(IMAGE):latest

# Removes every local image of this app, including the current :dev and :latest.
.PHONY: docker-clean
docker-clean:
	docker image ls -q \
		--filter label=$(IMAGE_LABEL) \
		| sort -u \
		| xargs -r docker image rm -f

# Removes only old untagged images of this app, keeping the current :dev and :latest.
.PHONY: docker-prune
docker-prune:
	docker image prune \
		--force \
		--filter dangling=true \
		--filter label=$(IMAGE_LABEL)
