# Health Value Dashboard

A demo Shiny for Python dashboard for surgical value metrics. It uses made-up data only.

## Layout

- `app/app.py`: the Shiny app object, UI, and server.
- `app/schema.py`: the column list and column name constants.
- `app/data.py`: loads and checks a CSV of cases.
- `app/stats.py`: means with 95% confidence intervals, headline numbers, and the per-surgeon summary.
- `app/store.py`: finds the data file and reloads it, keeping the last good copy.
- `app/filters.py`: applies the filter bar selections to the cases.
- `app/value_tab.py`, `app/data_tab.py`: the Value and Data tabs.
- `scripts/generate_data.py`: generates the made-up `data/sample.csv`.
- `data/sample.csv`: the sample data set used by the app and tests.
- `reference/compute.R`: base R reference for every statistic; writes `tests/golden/`.
- `tests/golden/`: R results that `tests/test_golden.py` checks Python against.
- `tests/`: pytest tests, one `test_<module>.py` per module.

## Make Targets

- `make install`: install dependencies with uv.
- `make format`: format and auto-fix with ruff.
- `make lint`: check formatting and lint with ruff.
- `make test`: run pytest.
- `make pre-pr`: format, lint, and test. Run before every PR.
- `make data`: regenerate `data/sample.csv`.
- `make reference`: rerun the R reference in Docker and rewrite `tests/golden/`.
- `make run`: serve the app at http://localhost:8000 with reload.
- `make docker-build`: build the image as `health-value-dashboard:dev`.
- `make docker-run-dev`: run `health-value-dashboard:dev` at http://localhost:8000, data in `.hvd-data/`.
- `make docker-run`: pull and run `ghcr.io/tahardi/health-value-dashboard:latest` the same way.

## Rules

- Screens and stats use `app/schema.py` constants, never column names.
- Every statistic has an R golden test.
- Never commit real data.
