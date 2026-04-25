#!/usr/bin/env bash
# run_all_offline.sh
# Corre los 4 scripts offline en orden.
#
# Uso:
#   DATA_DIR=./data \
#   MODELS_DIR=./backend/app/analytics/models \
#   REDIS_URL=redis://localhost:6379 \
#   bash backend/scripts/agents/offline/run_all_offline.sh

set -euo pipefail

cd "$(dirname "$0")"

echo "DATA_DIR   = ${DATA_DIR:-./data}"
echo "MODELS_DIR = ${MODELS_DIR:-./backend/app/analytics/models}"
echo "REDIS_URL  = ${REDIS_URL:-redis://localhost:6379}"
echo ""

python 01_train_conductual.py
python 02_train_transaccional.py
python 03_train_salud_financiera.py
python 04_build_fichas_redis.py

echo ""
echo "=========================================="
echo "  TODOS LOS MODELOS Y FICHAS CONSTRUIDOS"
echo "=========================================="
