.RECIPEPREFIX := >

.PHONY: up dev format test evals

up:
>docker compose -f infrastructure/docker-compose.yml up --build

dev:
>cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

format:
>cd backend && uv run ruff check --fix app tests
>cd backend && uv run ruff format app tests

test:
>cd backend && uv run pytest -q

evals:
>cd backend && uv run python -m app.evals.framework
