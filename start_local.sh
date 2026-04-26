#!/bin/bash
# ══════════════════════════════════════════════════════
# start_local.sh — Levanta Havi localmente para demo
# Requisitos: Python 3.11+, Node 18+, Redis corriendo
# ══════════════════════════════════════════════════════
set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}▶ Havi × Hey Banco — Arranque Local${NC}"
echo ""

# Verificar .env
if [ ! -f .env ]; then
  echo -e "${YELLOW}⚠  No encontré .env — copiando .env.example${NC}"
  cp .env.example .env
  echo -e "${YELLOW}   Edita .env con tu OPENAI_API_KEY antes de continuar.${NC}"
  exit 1
fi

# Verificar Redis
echo -e "${BLUE}▶ Verificando Redis...${NC}"
redis-cli ping > /dev/null 2>&1 || {
  echo "  Redis no está corriendo. Iniciando con Docker..."
  docker run -d -p 6379:6379 --name havi-redis redis:7-alpine 2>/dev/null || true
  sleep 2
}

# Backend
echo ""
echo -e "${BLUE}▶ Iniciando backend (FastAPI)...${NC}"
cd backend
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -e . -q 2>/dev/null || pip install -r requirements.txt -q
cd ..
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Esperar backend
echo "  Esperando backend..."
sleep 4

# Frontend
echo ""
echo -e "${BLUE}▶ Iniciando frontend (Vite)...${NC}"
cd frontend-demo
npm install -q 2>/dev/null || true
npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"
cd ..

echo ""
echo -e "${GREEN}✅ Sistema levantado:${NC}"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Ctrl+C para detener todo."

# Esperar y limpiar al salir
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Detenido.'" INT
wait
