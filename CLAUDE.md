# Health Value Dashboard

A demo Shiny for Python dashboard for surgical value metrics. It uses made-up data only.

## Layout

- `app/app.py`: the Shiny app object, UI, and server.
- `app/schema.py`: the column list and column name constants.
- `app/data.py`: loads and checks a CSV of cases.
- `scripts/generate_data.py`: generates the made-up `data/sample.csv`.
- `data/sample.csv`: the sample data set used by the app and tests.
- `tests/`: pytest tests, one `test_<module>.py` per module.

## Make Targets

- `make install`: install dependencies with uv.
- `make format`: format and auto-fix with ruff.
- `make lint`: check formatting and lint with ruff.
- `make test`: run pytest.
- `make pre-pr`: format, lint, and test. Run before every PR.
- `make data`: regenerate `data/sample.csv`.
- `make run`: serve the app at http://localhost:8000 with reload.

## Rules

- Screens and stats use `app/schema.py` constants, never column names.
- Every statistic has an R golden test.
- Never commit real data.
