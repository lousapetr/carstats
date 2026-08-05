# ---- frontend build ----
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- backend runtime ----
FROM python:3.12-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app/backend
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY backend/ ./
RUN uv sync --locked --no-dev

COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

ENV CARSTATS_FRONTEND_DIST_DIR=/app/frontend/dist \
    CARSTATS_DATABASE_URL=sqlite:////app/data/carstats.db \
    CARSTATS_UPLOADS_DIR=/app/data/uploads \
    PATH="/app/backend/.venv/bin:$PATH"

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
