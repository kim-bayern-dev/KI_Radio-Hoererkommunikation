FROM python:3.12-slim-bookworm

ENV POETRY_VERSION=2.1.1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME=/opt/poetry

# Install Poetry in a single layer
RUN apt-get update && apt-get install -y curl \
 && curl -sSL https://install.python-poetry.org | python - --version $POETRY_VERSION \
 && ln -s $POETRY_HOME/bin/poetry /usr/local/bin/poetry \
 && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy only dependency descriptors first to leverage Docker-layer caching
COPY pyproject.toml poetry.lock* ./

# Install only runtime deps (omit dev / tests) and skip installing the project itself
RUN poetry install --only main --no-root --no-interaction --no-ansi && poetry cache clear --all pypi

# ---- Application code ------------------------------------------------------
COPY src/ ./src
COPY assets/ ./assets
COPY config-kesselbach.yaml ./

EXPOSE 7860
CMD ["poetry", "run", "python", "src/app.py", "--config", "config-kesselbach.yaml"]
