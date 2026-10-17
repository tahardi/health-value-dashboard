FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/tahardi/health-value-dashboard

COPY --from=ghcr.io/astral-sh/uv:0.12.22 /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && uv sync --frozen --no-dev --no-install-project \
    && apt-get purge -y --auto-remove g++ \
    && rm -rf /var/lib/apt/lists/*

COPY app/ app/
COPY data/sample.csv /app/data/sample.csv

RUN useradd --create-home app \
    && mkdir /data \
    && chown app:app /data

ENV DATA_PATH=/data/current.csv SAMPLE_PATH=/app/data/sample.csv

USER app

VOLUME /data
EXPOSE 8000

CMD ["/app/.venv/bin/shiny", "run", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
