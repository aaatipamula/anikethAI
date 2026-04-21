# syntax = docker/dockerfile:experimental
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /home/bot/

COPY pyproject.toml uv.lock ./

# RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

COPY . .

CMD [ "uv", "run", "./src/main.py" ]
