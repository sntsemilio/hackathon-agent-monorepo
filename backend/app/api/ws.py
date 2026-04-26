"""
backend/app/api/ws.py
======================

WebSocket endpoint para notificaciones proactivas.
Envía insights generados por ProactiveEngine al frontend.

Endpoint: ws://localhost:8080/ws/notifications/{user_id}
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import time
from typing import Any, Dict, List, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Active connections per user
_connections: Dict[str, Set[WebSocket]] = {}


# ---------------------------------------------------------------------------
# Proactive insights templates
# ---------------------------------------------------------------------------
PROACTIVE_TEMPLATES = [
    {
        "type": "proactive_insight",
        "title": "Cargo recurrente detectado",
        "body": "Detectamos un cargo de ${amount} en {merchant} que se repite mensualmente. ¿Quieres revisarlo?",
        "action_card": {"id": "revisar_cargo", "title": "Revisar cargo", "deep_link": "/movimientos"},
        "merchants": ["Spotify", "Netflix", "Amazon Prime", "YouTube Premium", "Disney+"],
    },
    {
        "type": "proactive_insight",
        "title": "Oportunidad de ahorro",
        "body": "Este mes has gastado {pct}% menos en {category}. ¿Quieres mover ese excedente a inversión?",
        "action_card": {"id": "inversion_hey", "title": "Invertir excedente", "deep_link": "/inversion"},
        "categories": ["entretenimiento", "delivery", "compras en línea"],
    },
    {
        "type": "proactive_insight",
        "title": "Rendimiento de tu inversión",
        "body": "Tu inversión Hey ha generado ${amount} este mes. GAT nominal: {gat}%.",
        "action_card": {"id": "ver_inversion", "title": "Ver inversión", "deep_link": "/inversion"},
    },
    {
        "type": "proactive_insight",
        "title": "Fecha de corte próxima",
        "body": "Tu tarjeta Hey corta en 3 días. Saldo actual: ${amount}. ¿Quieres pagar ahora?",
        "action_card": {"id": "pagar_tarjeta", "title": "Pagar tarjeta", "deep_link": "/credito"},
    },
    {
        "type": "proactive_insight",
        "title": "Cashback disponible",
        "body": "Tienes ${amount} de cashback Hey Pro acumulado. ¿Quieres aplicarlo?",
        "action_card": {"id": "cashback", "title": "Aplicar cashback", "deep_link": "/pro/cashback"},
    },
]


def _generate_insight(user_id: str) -> Dict[str, Any]:
    """Genera un insight proactivo sintético basado en el user_id."""
    rng = random.Random(int.from_bytes(
        hashlib.sha256(f"{user_id}{time.time():.0f}".encode()).digest()[:8], "big"
    ))
    template = rng.choice(PROACTIVE_TEMPLATES)
    amount = round(rng.uniform(50, 5000), 2)
    insight = {
        "type": template["type"],
        "title": template["title"],
        "body": template["body"]
            .replace("${amount}", f"{amount:,.2f}")
            .replace("{merchant}", rng.choice(template.get("merchants", ["Servicio"])))
            .replace("{pct}", str(rng.randint(10, 35)))
            .replace("{category}", rng.choice(template.get("categories", ["general"])))
            .replace("{gat}", str(round(rng.uniform(9, 14), 2))),
        "action_card": template.get("action_card", {}),
        "timestamp": time.time(),
        "user_id": user_id,
    }
    return insight


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------
@router.websocket("/ws/notifications/{user_id}")
async def notifications_ws(websocket: WebSocket, user_id: str) -> None:
    await websocket.accept()
    _connections.setdefault(user_id, set()).add(websocket)
    logger.info("WS connected: user=%s", user_id)

    try:
        # Send initial greeting
        await websocket.send_json({
            "type": "connected",
            "message": f"Conectado a notificaciones para {user_id}",
            "timestamp": time.time(),
        })

        # Proactive insight loop (configurable interval)
        interval = 30  # seconds
        while True:
            await asyncio.sleep(interval)
            insight = _generate_insight(user_id)
            await websocket.send_json(insight)
            logger.debug("WS insight sent: user=%s title=%s", user_id, insight["title"])

    except WebSocketDisconnect:
        logger.info("WS disconnected: user=%s", user_id)
    except Exception:
        logger.exception("WS error: user=%s", user_id)
    finally:
        _connections.get(user_id, set()).discard(websocket)


async def push_to_user(user_id: str, message: Dict[str, Any]) -> int:
    """Push a message to all active WebSocket connections for a user."""
    conns = _connections.get(user_id, set())
    sent = 0
    dead: List[WebSocket] = []
    for ws in conns:
        try:
            await ws.send_json(message)
            sent += 1
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.discard(ws)
    return sent
