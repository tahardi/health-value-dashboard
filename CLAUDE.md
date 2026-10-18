# Health Value Dashboard

A demo Shiny for Python dashboard for surgical value metrics. It uses made-up data only.

## Layout

- `app/app.py`: the Shiny app object, UI, and server.
- `app/schema.py`: the column list and column name constants.
- `app/data.py`: loads and checks a CSV of cases.
- `app/stats.py`: means with 95% confidence intervals, headline numbers, and the per-surgeon summary.
- `app/store.py`: finds the data file and reloads it, keeping the last good copy.
- `app/filters.py`: applies the filter bar selections to the cases.
- `app/charts.py`: the cost versus function gain value map.
- `app/tables.py`: formats the per-surgeon summary for display.
- `app/value_tab.py`, `app/surgeons_tab.py`, `app/data_tab.py`: the Value, Surgeons, and Data tabs.
- `scripts/generate_data.py`: generates the made-up `data/sample.csv`.
- `scripts/screenshots.py`: runs the app and saves the README screenshots to `docs/screenshots/`.
- `data/sample.csv`: the sample data set used by the app and tests.
- `reference/compute.R`: base R reference for every statistic; writes `tests/golden/`.
- `tests/golden/`: R results that `tests/test_golden.py` checks Python against.
- `tests/`: pytest tests, one `test_<module>.py` per module.

## Make Targets

- `make install`: install dependencies with uv.
- `make format`: format and auto-fix with ruff.
- `make lint`: check formatting and lint with ruff.
- `make test`: run pytest.
- `make pre-pr` (the default target): install, regenerate the data and R golden files, format, lint, test, and build the image. Run before every PR.
- `make data`: regenerate `data/sample.csv`.
- `make reference`: rerun the R reference in Docker and rewrite `tests/golden/`.
- `make screenshots`: rewrite `docs/screenshots/` with Playwright (needs `uv run playwright install chromium` once).
- `make run`: serve the app at http://localhost:8000 with reload.
- `make docker-build`: build the image as `health-value-dashboard:dev`.
- `make docker-run-local`: run `health-value-dashboard:dev` at http://localhost:8000, data in `.hvd-data/`.
- `make docker-run-registry`: pull and run `ghcr.io/tahardi/health-value-dashboard:latest` the same way.
- `make docker-clean`: remove every local image of this app.
- `make docker-prune`: remove old untagged images of this app, keeping the current `:dev` and `:latest`.

## When make reference fails locally

If `make reference` fails on your machine, do not block on it. Run `make install data format lint test docker-build`
instead of `make pre-pr`, then push and let CI's `reference` job run R on Linux. If that job fails because
`tests/golden/` is out of date, run `gh run download <run-id> -n golden -D tests/golden`, commit the files, and push
again. Never edit golden files by hand.

## Rules

- Screens and stats use `app/schema.py` constants, never column names.
- Every statistic has an R golden test.
- Never commit real data.
