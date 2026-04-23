#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${1:-hackathon-redis}"
IMAGE="redis/redis-stack-server:7.2.0-v15"

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Redis container '${CONTAINER_NAME}' is already running."
  exit 0
fi

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  docker start "${CONTAINER_NAME}" >/dev/null
else
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -p 6379:6379 \
    "${IMAGE}" >/dev/null
fi

echo "Redis Stack is available at redis://localhost:6379"
