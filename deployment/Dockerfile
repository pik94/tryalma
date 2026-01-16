FROM python:3.13.1-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential dnsutils \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://astral.sh/uv/0.5.29/install.sh -o /uv-installer.sh \
    && echo "ca7c538ca905ef6682318e42221a99ec53c8c18db25eced18764854984002660  /uv-installer.sh" \
    sha256sum -c -

RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .

# Test
FROM builder AS test

WORKDIR /app

RUN uv sync --all-extras --frozen

CMD ["make", "test"]

# Dev app
FROM python:3.13.1-slim-bookworm AS app

COPY --from=builder /root/.local/bin /usr/local/bin
COPY --from=builder /app /app
ENV PATH="/usr/local/bin:$PATH"
RUN mkdir -p /var/www/.cache/uv \
    && chown -R 33:33 /var/www/.cache \
    && chown -R 33:33 /app/.venv/lib \
    && chown -R 33:33 /app

USER 33

WORKDIR /app

ENV PROMETHEUS_MULTIPROC_DIR=/app

CMD ["uv", "run", "--no-sync", "gunicorn", \
     "-k", "uvicorn.workers.UvicornH11Worker", \
     "-b", "0.0.0.0:8000", \
     "--workers", "8", \
     "service.web_app:app"]
