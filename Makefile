.RECIPEPREFIX := >

.PHONY: up dev deploy

up:
>docker compose up --build

dev:
>cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

deploy:
>bash infrastructure/deploy_gcp.sh
