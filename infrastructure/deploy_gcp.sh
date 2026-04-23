#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID before running deploy}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${GCP_SERVICE_NAME:-hackathon-agent-backend}"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "Building backend image: ${IMAGE}"
docker build -t "${IMAGE}" backend

echo "Configuring Docker auth for gcr.io"
gcloud auth configure-docker --quiet

echo "Pushing image"
docker push "${IMAGE}"

echo "Deploying Cloud Run service: ${SERVICE_NAME}"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "REDIS_URL=${REDIS_URL:-redis://<redis-host>:6379/0},REDIS_INDEX_NAME=${REDIS_INDEX_NAME:-hackathon_docs},REDIS_PREFIX=${REDIS_PREFIX:-doc:},REDIS_VECTOR_DIMS=${REDIS_VECTOR_DIMS:-1536},MCP_HOST=${MCP_HOST:-localhost},MCP_PORT=${MCP_PORT:-8765}"

echo "Cloud Run deployment complete."
