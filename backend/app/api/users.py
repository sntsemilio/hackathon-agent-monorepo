"""
backend/app/api/users.py
========================

User management endpoints for the Havi agent.
Currently provides demo users for the datathon UI.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

# Demo users for datathon — same data as frontend lib/users.ts
DEMO_USERS: List[Dict[str, Any]] = [
    {
        "user_id": "USR-00001",
        "name": "Carla Mendoza",
        "avatar": "👩‍💻",
        "description": "Actividad atípica · Presión financiera",
        "segment_labels": ["actividad_atipica_alerta", "presion_financiera"],
        "sample_questions": [
            "¿Por qué me bloquearon una transacción?",
            "¿Cómo puedo desbloquear mi tarjeta?",
            "¿Cuál es mi saldo actual?",
            "¿Mis datos están seguros?",
        ],
    },
    {
        "user_id": "USR-00042",
        "name": "Javier López",
        "avatar": "👨‍💼",
        "description": "Profesional · Inversor activo",
        "segment_labels": ["profesional_prospero_inversor", "activo_saludable"],
        "sample_questions": [
            "¿Cuál es mi rendimiento en inversiones este mes?",
            "¿Qué productos de inversión me recomiendas?",
            "¿Cuál es el GAT real de mi cuenta?",
            "¿Puedo abrir un fondo indexado?",
        ],
    },
    {
        "user_id": "USR-00108",
        "name": "Ana Torres",
        "avatar": "👩‍🎓",
        "description": "Joven digital · Hey Pro",
        "segment_labels": ["joven_digital_hey_pro", "en_construccion_crediticia"],
        "sample_questions": [
            "¿Cuánto cashback acumulé este mes?",
            "¿Qué hay de nuevo en Hey Shop?",
            "¿Cómo activo CoDi?",
            "¿Puedo subir mi límite de crédito?",
        ],
    },
    {
        "user_id": "USR-00205",
        "name": "Roberto Sánchez",
        "avatar": "👨‍🔧",
        "description": "Cliente estable · Perfil promedio",
        "segment_labels": ["cliente_promedio_estable", "activo_saludable"],
        "sample_questions": [
            "¿Cuál es mi saldo?",
            "¿Puedo hacer una transferencia?",
            "¿Qué beneficios tengo con mi cuenta?",
            "¿Cómo activo Hey Pro?",
        ],
    },
    {
        "user_id": "USR-00310",
        "name": "María González",
        "avatar": "👩‍💼",
        "description": "Estrés financiero · Necesita apoyo",
        "segment_labels": ["usuario_estres_financiero", "presion_financiera"],
        "sample_questions": [
            "¿Puedo reestructurar mi deuda?",
            "¿Cuánto debo en total?",
            "¿Hay algún plan de pagos disponible?",
            "¿Puedo pausar un pago?",
        ],
    },
    {
        "user_id": "USR-00415",
        "name": "Carlos Mendivil",
        "avatar": "🧑‍💻",
        "description": "Usuario básico · Nuevo cliente",
        "segment_labels": ["usuario_basico_bajo_enganche", "solido_sin_credito"],
        "sample_questions": [
            "¿Cómo funciona la cuenta Hey?",
            "¿Cómo deposito dinero?",
            "¿Hay comisiones?",
            "¿Puedo solicitar una tarjeta de crédito?",
        ],
    },
    {
        "user_id": "USR-00520",
        "name": "Daniela Ruiz",
        "avatar": "👩‍🎨",
        "description": "Empresaria · Alto volumen",
        "segment_labels": ["empresario_alto_volumen", "activo_saludable"],
        "sample_questions": [
            "¿Cómo configuro nómina para mi empresa?",
            "¿Puedo facturar desde Hey?",
            "¿Hay crédito PYME disponible?",
            "¿Cómo muevo grandes volúmenes?",
        ],
    },
    {
        "user_id": "USR-00630",
        "name": "Luis Fernández",
        "avatar": "👨‍🌾",
        "description": "Ahorrador · Construcción crediticia",
        "segment_labels": ["en_construccion_crediticia", "consumidor_digital_ocio"],
        "sample_questions": [
            "¿Cómo mejoro mi score buró?",
            "¿Cuánto he ahorrado este mes?",
            "¿Me conviene una tarjeta garantizada?",
            "¿Cuál es mi historial de pagos?",
        ],
    },
]


@router.get("")
async def list_demo_users() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get the list of demo users for the datathon UI.
    Each user includes segment labels and sample questions.
    """
    return {"users": DEMO_USERS}
