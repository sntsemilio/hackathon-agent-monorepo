"""
backend/app/agents/teams/tool_ops/agents.py
============================================

Tool operations del agente Havi. Cada tool devuelve datos realistas
y una respuesta personalizada al segmento conductual del usuario.

Tools disponibles:
  - saldo            : balance de cuenta débito + crédito disponible
  - movimientos      : últimos 5 movimientos según categorías de gasto
  - transferencia    : confirmación de transferencia (pendiente de validación)
  - cashback         : resumen de cashback acumulado (Hey Pro)
  - inversiones      : portafolio y rendimiento
  - ahorro           : progreso de metas de ahorro
  - limite_credito   : límite y crédito disponible
  - nomina           : resumen de nómina empresarial
  - bloqueo          : bloqueo/reporte de tarjeta
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Datos mock por usuario — consistentes con ficha_mock del frontend
# ---------------------------------------------------------------------------
_USER_DATA: Dict[str, Dict[str, Any]] = {
    "USR-00001": {  # Carla — actividad atípica, presión financiera
        "nombre": "Carla",
        "saldo_debito": 8_450.00,
        "saldo_credito": 1_100.00,
        "limite_credito": 10_000.00,
        "ahorro": 2_100.00,
        "inversion": 0.00,
        "cashback_acumulado": 48.50,
        "cashback_mes": 12.30,
        "movimientos": [
            ("Walmart Supercenter", -1_240.00, "hoy"),
            ("Gasolinería PEMEX", -680.00, "ayer"),
            ("OXXO Conveniencia", -145.00, "ayer"),
            ("Transferencia recibida", +3_500.00, "lunes"),
            ("Pago mínimo tarjeta", -450.00, "domingo"),
        ],
        "nomina_empleados": 0,
        "segmento": "actividad_atipica_alerta",
    },
    "USR-00042": {  # Javier — inversor profesional
        "nombre": "Javier",
        "saldo_debito": 45_320.00,
        "saldo_credito": 85_000.00,
        "limite_credito": 100_000.00,
        "ahorro": 45_000.00,
        "inversion": 250_000.00,
        "rendimiento_mes": 1.8,        # %
        "rendimiento_anual": 14.2,     # %
        "gat_real": 11.4,
        "cashback_acumulado": 1_820.00,
        "cashback_mes": 210.00,
        "movimientos": [
            ("Inversión Hey — aporte", -10_000.00, "hoy"),
            ("Restaurante Pujol", -2_340.00, "ayer"),
            ("Aeromexico — vuelo CDG", -18_600.00, "viernes"),
            ("Transferencia recibida SPEI", +55_000.00, "jueves"),
            ("Amazon Prime — suscripción", -249.00, "miércoles"),
        ],
        "nomina_empleados": 0,
        "segmento": "profesional_prospero_inversor",
    },
    "USR-00108": {  # Ana — joven digital Hey Pro
        "nombre": "Ana",
        "saldo_debito": 12_680.00,
        "saldo_credito": 3_000.00,
        "limite_credito": 5_000.00,
        "ahorro": 8_500.00,
        "inversion": 5_000.00,
        "cashback_acumulado": 342.80,
        "cashback_mes": 68.50,
        "cashback_proyectado": 95.00,
        "movimientos": [
            ("Netflix", -219.00, "hoy"),
            ("Rappi — comida a domicilio", -385.00, "ayer"),
            ("Steam — videojuegos", -599.00, "sábado"),
            ("Spotify Premium", -99.00, "viernes"),
            ("Uber Eats", -245.00, "jueves"),
        ],
        "nomina_empleados": 0,
        "segmento": "joven_digital_hey_pro",
    },
    "USR-00205": {  # Roberto — cliente estable
        "nombre": "Roberto",
        "saldo_debito": 18_200.00,
        "saldo_credito": 5_000.00,
        "limite_credito": 12_000.00,
        "ahorro": 12_000.00,
        "inversion": 8_000.00,
        "cashback_acumulado": 185.00,
        "cashback_mes": 32.00,
        "movimientos": [
            ("CFE — pago de luz", -980.00, "hoy"),
            ("Superama", -1_450.00, "ayer"),
            ("Colegiatura mensual", -4_200.00, "jueves"),
            ("Telmex — internet", -599.00, "miércoles"),
            ("OXXO Gas", -700.00, "martes"),
        ],
        "nomina_empleados": 0,
        "segmento": "cliente_promedio_estable",
    },
    "USR-00310": {  # María — estrés financiero
        "nombre": "María",
        "saldo_debito": 2_150.00,
        "saldo_credito": 0.00,
        "limite_credito": 22_000.00,
        "deuda_total": 22_000.00,
        "pago_minimo": 660.00,
        "ahorro": 1_200.00,
        "inversion": 0.00,
        "cashback_acumulado": 0.00,
        "cashback_mes": 0.00,
        "movimientos": [
            ("Renta mensual", -7_500.00, "ayer"),
            ("Farmacias del Ahorro", -380.00, "ayer"),
            ("CFE — luz", -620.00, "viernes"),
            ("Telmex", -399.00, "jueves"),
            ("OXXO — varios", -210.00, "martes"),
        ],
        "nomina_empleados": 0,
        "segmento": "usuario_estres_financiero",
    },
    "USR-00415": {  # Carlos — nuevo cliente
        "nombre": "Carlos",
        "saldo_debito": 3_890.00,
        "saldo_credito": 0.00,
        "limite_credito": 0.00,
        "ahorro": 3_500.00,
        "meta_ahorro": 10_000.00,
        "inversion": 0.00,
        "cashback_acumulado": 0.00,
        "cashback_mes": 0.00,
        "movimientos": [
            ("Walmart — supermercado", -890.00, "hoy"),
            ("Metro CDMX — recarga", -100.00, "ayer"),
            ("Farmacia Guadalajara", -245.00, "sábado"),
            ("OXXO — gas", -520.00, "viernes"),
            ("Depósito inicial", +5_000.00, "semana pasada"),
        ],
        "nomina_empleados": 0,
        "segmento": "usuario_basico_bajo_enganche",
    },
    "USR-00520": {  # Daniela — empresaria
        "nombre": "Daniela",
        "saldo_debito": 89_400.00,
        "saldo_credito": 35_000.00,
        "limite_credito": 80_000.00,
        "ahorro": 80_000.00,
        "inversion": 120_000.00,
        "rendimiento_mes": 1.6,
        "rendimiento_anual": 13.1,
        "gat_real": 10.8,
        "cashback_acumulado": 4_280.00,
        "cashback_mes": 890.00,
        "movimientos": [
            ("Proveedor Materiales SA", -32_500.00, "hoy"),
            ("Aeromexico Negocios", -8_900.00, "ayer"),
            ("Microsoft 365 Business", -2_800.00, "viernes"),
            ("Cobro cliente — factura 482", +65_000.00, "jueves"),
            ("Nómina quincenal — 15 empleados", -87_500.00, "miércoles"),
        ],
        "nomina_empleados": 15,
        "nomina_quincenal": 87_500.00,
        "segmento": "empresario_alto_volumen",
    },
    "USR-00630": {  # Luis — construyendo historial
        "nombre": "Luis",
        "saldo_debito": 15_750.00,
        "saldo_credito": 2_000.00,
        "limite_credito": 3_000.00,
        "ahorro": 15_000.00,
        "meta_ahorro": 25_000.00,
        "inversion": 2_000.00,
        "cashback_acumulado": 95.00,
        "cashback_mes": 18.00,
        "score_buro_estimado": "650-700 (bueno, en ascenso)",
        "movimientos": [
            ("Cinépolis", -280.00, "hoy"),
            ("Domino's Pizza", -320.00, "ayer"),
            ("Shein — ropa", -680.00, "sábado"),
            ("Spotify", -99.00, "viernes"),
            ("Pago puntual tarjeta Hey", -500.00, "jueves"),
        ],
        "nomina_empleados": 0,
        "segmento": "en_construccion_crediticia",
    },
}


def _get_user_data(user_id: str) -> Dict[str, Any]:
    return _USER_DATA.get(user_id, {
        "nombre": "Cliente",
        "saldo_debito": 5_000.00,
        "saldo_credito": 2_000.00,
        "limite_credito": 5_000.00,
        "ahorro": 3_000.00,
        "inversion": 0.00,
        "cashback_acumulado": 0.00,
        "cashback_mes": 0.00,
        "movimientos": [],
        "nomina_empleados": 0,
        "segmento": "default",
    })


def _fmt(amount: float) -> str:
    return f"${amount:,.2f} MXN"


def _conductual(ficha: Dict[str, Any]) -> str:
    return (((ficha.get("segmentos") or {}).get("conductual") or {}).get("name") or "")


# ---------------------------------------------------------------------------
# Handlers por tipo de operación
# ---------------------------------------------------------------------------

def _handle_saldo(ud: Dict, ficha: Dict, intent: str) -> str:
    name = ud.get("nombre", "")
    debito = ud.get("saldo_debito", 0)
    credito = ud.get("saldo_credito", 0)
    seg = _conductual(ficha)

    base = f"Saldo disponible en débito: {_fmt(debito)}."

    if ud.get("limite_credito", 0) > 0:
        base += f" Crédito disponible: {_fmt(credito)} de {_fmt(ud['limite_credito'])} de límite."

    # Comentario personalizado por segmento
    if seg == "actividad_atipica_alerta":
        return (base + " Por la actividad inusual reciente en tu cuenta, te recomiendo "
                "revisar tus últimos movimientos para confirmar que todo esté en orden.")
    if seg == "profesional_prospero_inversor":
        inv = ud.get("inversion", 0)
        return (base + f" Además tienes {_fmt(inv)} en portafolio de inversiones. "
                f"¿Quieres ver el rendimiento del mes?")
    if seg == "usuario_estres_financiero":
        deuda = ud.get("deuda_total", 0)
        pago_min = ud.get("pago_minimo", 0)
        return (base + f" Tu deuda actual es de {_fmt(deuda)}. "
                f"El pago mínimo esta quincena es {_fmt(pago_min)}. "
                "¿Quieres explorar opciones de reestructuración?")
    if seg == "usuario_basico_bajo_enganche":
        ahorro = ud.get("ahorro", 0)
        meta = ud.get("meta_ahorro", 10_000)
        pct = int((ahorro / meta) * 100) if meta else 0
        return (base + f" En tu fondo de ahorro tienes {_fmt(ahorro)} "
                f"— ya llevas {pct}% de tu meta de {_fmt(meta)}. ¡Vas muy bien!")
    if seg == "empresario_alto_volumen":
        return (base + f" Recuerda que la nómina quincenal de tus {ud.get('nomina_empleados', 0)} "
                f"empleados es de {_fmt(ud.get('nomina_quincenal', 0))}. "
                "¿Quieres programar el pago?")
    if seg == "en_construccion_crediticia":
        return (base + f" Tu crédito disponible es {_fmt(credito)}. "
                "Mantenerlo por debajo del 30% de tu límite mejora tu score en buró. ¡Lo estás haciendo bien!")
    return base + " ¿Necesitas algo más?"


def _handle_movimientos(ud: Dict, ficha: Dict) -> str:
    movs = ud.get("movimientos") or []
    name = ud.get("nombre", "")
    seg = _conductual(ficha)

    if not movs:
        return "No encontré movimientos recientes en tu cuenta."

    lines = [f"Tus últimos {len(movs)} movimientos:"]
    for i, (desc, monto, fecha) in enumerate(movs, 1):
        signo = "+" if monto > 0 else ""
        lines.append(f"  {i}. {desc} — {signo}{_fmt(monto)} ({fecha})")

    summary = "\n".join(lines)

    if seg == "actividad_atipica_alerta":
        return summary + "\n\n¿Reconoces todos estos movimientos? Si algo te parece extraño, puedo ayudarte a reportarlo."
    if seg == "profesional_prospero_inversor":
        return summary + "\n\n¿Quieres que analice tus patrones de gasto del mes o ver el detalle de algún movimiento?"
    if seg == "usuario_estres_financiero":
        total_gastos = sum(m for _, m, _ in movs if m < 0)
        return (summary + f"\n\nTotal gastado en estos movimientos: {_fmt(abs(total_gastos))}. "
                "¿Te ayudo a identificar en qué podrías reducir gastos este mes?")
    if seg == "joven_digital_hey_pro":
        suscripciones = [d for d, _, _ in movs if any(x in d.lower() for x in ["netflix", "spotify", "apple", "steam", "disney"])]
        if suscripciones:
            return summary + f"\n\nTienes {len(suscripciones)} suscripciones activas. Con Hey Pro acumulas cashback en todas ellas. ¿Quieres ver cuánto llevas?"
    if seg == "empresario_alto_volumen":
        return summary + "\n\n¿Necesitas el estado de cuenta completo para facturación o quieres exportar los movimientos en CSV?"
    if seg == "en_construccion_crediticia":
        pagos = [(d, m) for d, m, _ in movs if "pago" in d.lower() and m < 0]
        if pagos:
            return summary + "\n\n¡Excelente! Tus pagos puntuales se están reportando a buró y están mejorando tu score gradualmente."
    return summary + "\n\n¿Quieres ver el detalle de algún movimiento?"


def _handle_transferencia(ud: Dict, ficha: Dict, intent: str) -> str:
    name = ud.get("nombre", "")
    seg = _conductual(ficha)
    debito = ud.get("saldo_debito", 0)

    if seg == "actividad_atipica_alerta":
        return (f"Claro, puedo preparar tu transferencia. Tienes {_fmt(debito)} disponibles. "
                "Por la actividad inusual reciente, te recomiendo confirmar tu identidad primero — "
                "escribe 'verificar identidad' y lo hacemos en segundos. "
                "¿A qué cuenta y por qué monto quieres transferir?")

    if debito < 500:
        return (f"Tu saldo actual es {_fmt(debito)}, lo cual podría no ser suficiente "
                "para la transferencia. ¿Quieres confirmar el monto exacto que deseas enviar?")

    if seg == "empresario_alto_volumen":
        return (f"Listo para procesar tu transferencia. Tu saldo disponible es {_fmt(debito)}. "
                "Para montos mayores a $50,000 MXN aplica el límite de transferencia empresarial. "
                "¿Cuál es el monto y la cuenta destino?")

    return (f"Claro, puedo preparar tu transferencia. Tienes {_fmt(debito)} disponibles. "
            "¿A qué cuenta y por qué monto? Confirma los datos y lo procuro al instante.")


def _handle_cashback(ud: Dict, ficha: Dict) -> str:
    total = ud.get("cashback_acumulado", 0)
    mes = ud.get("cashback_mes", 0)
    seg = _conductual(ficha)
    name = ud.get("nombre", "")

    if total == 0 and mes == 0:
        return ("Aún no tienes cashback acumulado. Activa Hey Pro y empieza a ganar "
                "hasta 1% de devolución en todas tus compras. ¿Te explico cómo?")

    if seg == "joven_digital_hey_pro":
        proyectado = ud.get("cashback_proyectado", mes * 1.3)
        return (f"Este mes llevas {_fmt(mes)} de cashback acumulado. "
                f"Total histórico: {_fmt(total)}. "
                f"Si mantienes tu ritmo de compras, cerrarás el mes en ~{_fmt(proyectado)}. "
                "Tus suscripciones de streaming son las que más cashback generan — ¿sabías eso?")

    if seg == "profesional_prospero_inversor":
        return (f"Cashback acumulado este mes: {_fmt(mes)}. Total: {_fmt(total)}. "
                "Con tu nivel de gasto mensual, considera activar la cuenta maestra — "
                "el cashback sube a 2% en categorías premium.")

    return (f"Tienes {_fmt(mes)} de cashback acumulado este mes y {_fmt(total)} en total. "
            "Puedes canjearlo en Hey Shop o abonarlo a tu cuenta. ¿Cuál prefieres?")


def _handle_inversiones(ud: Dict, ficha: Dict) -> str:
    inv = ud.get("inversion", 0)
    seg = _conductual(ficha)
    name = ud.get("nombre", "")

    if inv == 0:
        if seg == "usuario_basico_bajo_enganche" or seg == "en_construccion_crediticia":
            return ("Aún no tienes inversiones activas. Con Inversión Hey puedes empezar "
                    "desde $100 MXN, con liquidez inmediata y sin comisiones. "
                    "¿Quieres que te explique cómo funciona?")
        return ("No tienes inversiones activas aún. ¿Te ayudo a conocer las opciones disponibles?")

    rendimiento_mes = ud.get("rendimiento_mes", 0)
    rendimiento_anual = ud.get("rendimiento_anual", 0)
    gat = ud.get("gat_real", 0)
    ganancia_mes = inv * (rendimiento_mes / 100)

    if seg == "profesional_prospero_inversor":
        return (f"Portafolio actual: {_fmt(inv)}. "
                f"Rendimiento este mes: +{rendimiento_mes}% ({_fmt(ganancia_mes)} MXN). "
                f"Rendimiento anualizado: {rendimiento_anual}%. GAT real: {gat}%. "
                "Tu portafolio supera la inflación por 3.2 puntos. "
                "¿Quieres explorar diversificar en CETES o fondos indexados para optimizarlo?")

    if seg == "empresario_alto_volumen":
        return (f"Inversiones activas: {_fmt(inv)}. "
                f"Rendimiento mensual: +{rendimiento_mes}% | GAT real: {gat}%. "
                "¿Consideraste mover parte del flujo de caja excedente a un instrumento "
                "de mayor rendimiento con liquidez a 28 días?")

    return (f"Tienes {_fmt(inv)} en inversiones con un rendimiento mensual de {rendimiento_mes}%. "
            "¿Quieres ver el desglose por instrumento?")


def _handle_ahorro(ud: Dict, ficha: Dict) -> str:
    ahorro = ud.get("ahorro", 0)
    meta = ud.get("meta_ahorro", 0)
    seg = _conductual(ficha)
    name = ud.get("nombre", "")

    if seg == "usuario_basico_bajo_enganche":
        pct = int((ahorro / meta) * 100) if meta else 0
        return (f"Tu fondo de ahorro tiene {_fmt(ahorro)}. "
                f"Llevas {pct}% de tu meta de {_fmt(meta)}. "
                "Con ahorro programado puedes apartar automáticamente cada quincena. "
                "¿Activo $500 automáticos y lo vas subiendo cuando puedas?")

    if seg == "en_construccion_crediticia":
        pct = int((ahorro / meta) * 100) if meta else 0
        falta = meta - ahorro
        return (f"¡Muy bien! Tienes {_fmt(ahorro)} ahorrados — {pct}% de tu meta de {_fmt(meta)}. "
                f"Te faltan {_fmt(falta)} para llegar. "
                "Además, reportar tus ahorros y pagos puntuales ayuda a tu score en buró. ¡Sigue así!")

    if seg == "usuario_estres_financiero":
        return (f"Tu fondo de emergencia actual es {_fmt(ahorro)}. "
                "Te recomiendo mantenerlo intacto por ahora y no usarlo para pagos de deuda. "
                "Un fondo de emergencia es tu red de seguridad. ¿Quieres que revisemos juntos el flujo del mes?")

    if seg == "profesional_prospero_inversor":
        return (f"Tienes {_fmt(ahorro)} en cuenta de ahorro. "
                "Con tu perfil, podrías mover una parte a Inversión Hey o CETES para "
                "obtener mejor rendimiento sin perder liquidez. ¿Te armo una simulación?")

    return f"Tu ahorro actual es {_fmt(ahorro)}. ¿Quieres configurar una meta o aumentar el ahorro automático?"


def _handle_limite_credito(ud: Dict, ficha: Dict) -> str:
    limite = ud.get("limite_credito", 0)
    disponible = ud.get("saldo_credito", 0)
    seg = _conductual(ficha)
    name = ud.get("nombre", "")

    if limite == 0:
        if seg == "usuario_basico_bajo_enganche":
            return ("Aún no tienes tarjeta de crédito. Con tu historial actual podrías "
                    "calificar para la tarjeta garantizada Hey — empiezas con $1,000 de límite "
                    "y lo vas subiendo con pagos puntuales. ¿Te interesa solicitarla?")
        return "Aún no tienes crédito activo. ¿Te explico las opciones disponibles?"

    utilizado = limite - disponible
    pct_utilizado = int((utilizado / limite) * 100) if limite else 0

    if seg == "usuario_estres_financiero":
        return (f"Límite total: {_fmt(limite)}. Utilizado: {_fmt(utilizado)} ({pct_utilizado}%). "
                "Estás usando más del 80% de tu crédito disponible, lo cual afecta tu score. "
                "¿Quieres que revisemos un plan para reducir la utilización gradualmente?")

    if seg == "joven_digital_hey_pro":
        return (f"Límite actual: {_fmt(limite)}. Disponible: {_fmt(disponible)} ({100-pct_utilizado}% libre). "
                "Para solicitar un aumento de límite necesitas 6 meses de pagos puntuales — "
                f"y llevas buen camino. ¿Cuándo fue tu último pago?")

    if seg == "en_construccion_crediticia":
        return (f"Límite: {_fmt(limite)} | Disponible: {_fmt(disponible)} | Utilizado: {pct_utilizado}%. "
                "Tip clave: mantén la utilización por debajo del 30% para mejorar tu score. "
                f"Ahora mismo estás en {pct_utilizado}%. "
                + ("¡Perfecto, sigue así!" if pct_utilizado < 30 else "¿Quieres un plan para bajarlo?"))

    return (f"Límite de crédito: {_fmt(limite)}. Disponible ahora: {_fmt(disponible)}. "
            f"Llevas {pct_utilizado}% utilizado este ciclo.")


def _handle_nomina(ud: Dict, ficha: Dict) -> str:
    empleados = ud.get("nomina_empleados", 0)
    monto = ud.get("nomina_quincenal", 0)
    seg = _conductual(ficha)

    if seg != "empresario_alto_volumen" or empleados == 0:
        return ("Para configurar nómina empresarial en Hey necesitas una cuenta de negocios activa. "
                "¿Tienes empleados a los que pagar actualmente?")

    return (f"Tienes configurada la nómina para {empleados} empleados. "
            f"El último pago fue de {_fmt(monto)} (quincena anterior). "
            "Puedes programar el próximo pago, agregar empleados o generar el CFDI de nómina. "
            "¿Qué necesitas hacer?")


def _handle_bloqueo(ud: Dict, ficha: Dict) -> str:
    seg = _conductual(ficha)

    if seg == "actividad_atipica_alerta":
        return ("Puedo bloquear tu tarjeta de inmediato desde aquí. "
                "El bloqueo es instantáneo y no cancela la tarjeta — puedes desbloquearla "
                "cuando quieras. ¿Confirmas que quieres bloquear tu tarjeta terminación 4821?")

    return ("Para bloquear o reportar tu tarjeta, confirma: ¿es la tarjeta de débito o crédito? "
            "El bloqueo es inmediato y gratuito. También puedo ayudarte a reportar un cargo no reconocido.")


def _handle_verificacion(ud: Dict, ficha: Dict) -> str:
    """Mock de verificación de identidad — siempre exitosa en demo."""
    name = ud.get("nombre", "")
    return (
        f"✅ ¡Identidad verificada correctamente, {name}! "
        "Tu sesión está autenticada y puedes operar con total normalidad. "
        "Ya puedes hacer transferencias, consultar movimientos y cualquier operación. "
        "¿Qué necesitas hacer?"
    )


# ---------------------------------------------------------------------------
# Dispatcher principal
# ---------------------------------------------------------------------------

async def tool_ops_node(state: Dict[str, Any]) -> Dict[str, Any]:
    profile = state.get("profile") or {}
    intent = (profile.get("intent") or "").lower()
    user_id = state.get("user_id") or ""
    ficha = state.get("ficha_cliente") or {}

    ud = _get_user_data(user_id)

    # Detectar tipo de operación por keywords en intent
    text = _dispatch(intent, ud, ficha)

    return {
        "draft_response_text": text,
        "draft_meta": {
            "source": "tool_ops",
            "tool": _detect_tool(intent),
            "user_id": user_id,
        },
    }


def _detect_tool(intent: str) -> str:
    if any(k in intent for k in ("verificar", "verificacion", "verificación",
                                  "confirmar identidad", "autenticar", "soy yo", "confirmo")):
        return "verificacion_identidad"
    if any(k in intent for k in ("cashback", "puntos", "recompensa")):
        return "cashback"
    if any(k in intent for k in ("inversion", "rendimiento", "portafolio", "fondo", "gat")):
        return "inversiones"
    if any(k in intent for k in ("ahorro", "meta", "ahorros")):
        return "ahorro"
    if any(k in intent for k in ("limite", "cupo", "credito disponible")):
        return "limite_credito"
    if any(k in intent for k in ("nomina", "nómina", "empleados")):
        return "nomina"
    if any(k in intent for k in ("bloqueo", "reportar", "cancelar tarjeta")):
        return "bloqueo"
    if any(k in intent for k in ("transferencia", "transferir", "enviar")):
        return "transferencia"
    if any(k in intent for k in ("movimiento", "historial", "gastos", "extracto", "ultimas compras")):
        return "movimientos"
    if any(k in intent for k in ("saldo", "balance", "cuanto tengo")):
        return "saldo"
    return "general"


def _dispatch(intent: str, ud: Dict, ficha: Dict) -> str:
    # Verificación de identidad — siempre primero
    if any(k in intent for k in ("verificar", "verificacion", "verificación",
                                  "confirmar identidad", "autenticar", "soy yo", "confirmo")):
        return _handle_verificacion(ud, ficha)
    if any(k in intent for k in ("cashback", "puntos", "recompensa")):
        return _handle_cashback(ud, ficha)
    if any(k in intent for k in ("inversion", "rendimiento", "portafolio", "fondo", "gat")):
        return _handle_inversiones(ud, ficha)
    if any(k in intent for k in ("ahorro", "meta de ahorro", "ahorros")):
        return _handle_ahorro(ud, ficha)
    if any(k in intent for k in ("limite", "cupo", "credito disponible")):
        return _handle_limite_credito(ud, ficha)
    if any(k in intent for k in ("nomina", "nómina", "pagar empleados")):
        return _handle_nomina(ud, ficha)
    if any(k in intent for k in ("bloqueo", "reportar", "cancelar tarjeta")):
        return _handle_bloqueo(ud, ficha)
    if any(k in intent for k in ("transferencia", "transferir", "enviar")):
        return _handle_transferencia(ud, ficha, intent)
    if any(k in intent for k in ("movimiento", "historial", "gastos", "extracto",
                                  "ultimas compras", "estado de cuenta")):
        return _handle_movimientos(ud, ficha)
    # Default: saldo
    return _handle_saldo(ud, ficha, intent)
