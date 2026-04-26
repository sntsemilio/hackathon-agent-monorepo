import { useState, useMemo, useEffect } from 'react'
import { useSSE } from './hooks/useSSE'
import { useUsers } from './hooks/useUsers'
import { ChatPanel } from './components/chat/ChatPanel'
import { FichaSidebar } from './components/ficha/FichaSidebar'
import { TracePanel } from './components/trace/TracePanel'
import { ObsDashboard } from './components/obs/ObsDashboard'
import LoginScreen from './components/login/LoginScreen'
import { DemoUser, Ficha } from './types'

// ---------------------------------------------------------------------------
// Saludos personalizados — Havi conoce a cada usuario desde el primer segundo
// ---------------------------------------------------------------------------
const GREETINGS: Record<string, string> = {
  'USR-00001': 'Hola Carla 👋 Detecté actividad inusual en tu cuenta recientemente. Puedes consultar tu saldo y movimientos normalmente. Para transferencias, solo escribe "verificar identidad" y te autenticamos en segundos. ¿Cómo te ayudo?',
  'USR-00042': 'Hola Javier 👋 Tu portafolio creció 1.8% este mes — tienes $250,000 MXN generando un GAT real de 11.4%. ¿Exploramos cómo optimizarlo o diversificarlo?',
  'USR-00108': '¡Hey Ana! 🙌 Llevas $342.80 MXN de cashback acumulado y vas muy bien para cerrar el mes en ~$95. Tus suscripciones de streaming son las que más cashback generan. ¿Qué necesitas hoy?',
  'USR-00205': 'Hola Roberto 👋 Todo en orden — tienes $18,200 MXN disponibles y tus servicios del mes están al corriente. ¿En qué te puedo ayudar?',
  'USR-00310': 'Hola María 👋 Estoy aquí para ayudarte, sin presión. Veo que tienes un pago mínimo de $660 MXN próximo. ¿Quieres que revisemos opciones de reestructuración juntos?',
  'USR-00415': '¡Hola Carlos! 👋 Bienvenido a Hey Banco. Ya tienes $3,500 MXN ahorrados — llevas el 35% de tu meta de $10,000. ¿Qué quieres explorar hoy?',
  'USR-00520': 'Hola Daniela 👋 La nómina quincenal de tus 15 empleados está programada. Tienes $89,400 MXN disponibles en cuenta empresarial. ¿Qué necesitas gestionar?',
  'USR-00630': 'Hola Luis 👋 Tu score en buró está en ascenso — tus pagos puntuales están teniendo efecto 📈 Tienes $15,000 MXN ahorrados, ¡vas muy bien! ¿Cómo te ayudo hoy?',
}

// ---------------------------------------------------------------------------
// Insights proactivos — Havi ya analizó la cuenta antes de que preguntes
// ---------------------------------------------------------------------------
const PROACTIVE_INSIGHTS: Record<string, string> = {
  'USR-00001': '🔒 Detecté un acceso desde un dispositivo nuevo el lunes a las 11:47 pm (Ciudad de México). ¿Fuiste tú? Si no lo reconoces, puedo bloquear el acceso ahora mismo.',
  'USR-00042': '💡 Oportunidad detectada: tienes $45,000 MXN en ahorro generando ~4% anual, mientras tu portafolio de inversión rinde 14.2%. Mover una parte podría generarte ~$4,500 MXN más al año.',
  'USR-00108': '✨ ¡Casi llegas al nivel Gold! Si gastas $280 MXN más en plataformas digitales este mes, tu cashback sube de 1% a 1.5% en todas tus compras. Te falta muy poco.',
  'USR-00205': '💳 Llevas 8 meses sin usar tu línea de crédito disponible ($7,000 MXN). Usarla y pagarla puntualmente puede aumentar tu límite hasta $12,000 MXN. ¿Quieres saber cómo?',
  'USR-00310': '⚠️ Patrón detectado: tus gastos en farmacia subieron 38% vs. el mes pasado ($380 vs $275 MXN). También tu renta representa el 58% de tus ingresos estimados este ciclo. ¿Te ayudo a revisar el flujo?',
  'USR-00415': '🎯 Llevas 3 meses con tu cuenta Hey y aún no has activado el ahorro automático. Con solo $200 MXN quincenales llegarías a tu meta de $10,000 en exactamente 10 meses. ¿Lo activamos?',
  'USR-00520': '📊 La nómina del próximo miércoles ($87,500 MXN) será tu mayor egreso del mes. Con tu flujo actual tienes cobertura, pero si adelantas el cobro de la factura 483 ($65,000 pendiente) quedas con holgura. ¿Programo un recordatorio?',
  'USR-00630': '📈 Buenas noticias: tu score en buró subió ~15 puntos este mes gracias a tus pagos puntuales. Si mantienes este ritmo 3 meses más, podrías calificar para un aumento de límite de crédito automático.',
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [selectedUserIdx, setSelectedUserIdx] = useState(0)
  const [personalizationEnabled, setPersonalizationEnabled] = useState(true)
  const [activeView, setActiveView] = useState<'chat' | 'obs'>('chat')
  const [mockFicha, setMockFicha] = useState<Ficha | null>(null)

  const { messages, currentTrace, ficha: sseficha, profile, isStreaming, sendMessage, clearMessages, greetUser } = useSSE()
  const { users } = useUsers()

  const selectedUser = useMemo(
    () => (users?.[selectedUserIdx] as DemoUser) || null,
    [users, selectedUserIdx]
  )

  // Cuando cambia el usuario seleccionado, carga la ficha_mock como fallback
  useEffect(() => {
    if (selectedUser?.ficha_mock) {
      setMockFicha(selectedUser.ficha_mock)
    }
  }, [selectedUser])

  // Saludo inicial al montar la app (primer usuario cargado)
  useEffect(() => {
    if (isAuthenticated && selectedUser) {
      greetUser(
        GREETINGS[selectedUser.user_id] || '',
        PROACTIVE_INSIGHTS[selectedUser.user_id]
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  // Prioriza la ficha real del SSE, si no está disponible usa la mock
  const ficha = sseficha || mockFicha

  const handleSend = (message: string) => {
    sendMessage(message, personalizationEnabled ? selectedUser?.user_id : null)
  }

  const handleUserChange = (userId: string) => {
    const idx = users?.findIndex((u) => u.id === userId) ?? 0
    const safeIdx = idx < 0 ? 0 : idx
    const targetUser = users?.[safeIdx]
    setSelectedUserIdx(safeIdx)
    // Set mock ficha immediately so the sidebar never flashes "cargando"
    if (targetUser?.ficha_mock) {
      setMockFicha(targetUser.ficha_mock)
    }
    // greetUser clears messages internally and animates greeting + proactive insight
    greetUser(GREETINGS[userId] || '', PROACTIVE_INSIGHTS[userId])
  }

  if (!isAuthenticated) {
    return <LoginScreen onEnter={() => setIsAuthenticated(true)} />
  }

  if (!selectedUser) {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
                         height: '100vh', background: '#0D1117', color: '#E2E8F0', fontFamily: 'Inter, sans-serif' }}>Loading...</div>
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column',
                  background: '#0D1117', color: '#E2E8F0', overflow: 'hidden', fontFamily: 'Inter, sans-serif' }}>

      {/* ── HEADER ────────────────────────── */}
      <header style={{
        height: '52px', flexShrink: 0, display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', padding: '0 16px',
        background: '#0D1117', borderBottom: '1px solid #21262D', boxShadow: '0 1px 3px rgba(0,0,0,0.3)'
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <img src="/hey-banco-logo.svg" alt="Hey Banco"
               style={{ height: '24px', width: 'auto' }}
               onError={e => (e.currentTarget.style.display = 'none')} />
          <span style={{ color: '#00C389', fontWeight: 800, fontSize: '16px',
                         letterSpacing: '-0.02em' }}>havi</span>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%',
                         background: '#00C389', display: 'inline-block', marginLeft: '6px' }} />
          <div style={{ width: '1px', height: '24px', background: '#21262D', marginLeft: '8px' }} />
        </div>

        {/* Tabs Chat / Obs */}
        <div style={{ display: 'flex', gap: '4px', background: '#161B22',
                      borderRadius: '10px', padding: '3px' }}>
          {(['chat','obs'] as const).map(v => (
            <button key={v} onClick={() => setActiveView(v)}
              style={{
                padding: '5px 14px', borderRadius: '8px', border: 'none',
                cursor: 'pointer', fontSize: '12px', fontWeight: 600,
                transition: 'all 180ms',
                background: activeView === v ? '#00C389' : 'transparent',
                color: activeView === v ? '#0D1117' : '#8B949E'
              }}>
              {v === 'chat' ? 'Chat' : 'Obs'}
            </button>
          ))}
        </div>

        {/* Derecha: toggle + user picker */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {activeView === 'chat' && (
            <>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px',
                              cursor: 'pointer', fontSize: '12px', color: '#8B949E' }}>
                <input type="checkbox" checked={personalizationEnabled}
                       onChange={e => setPersonalizationEnabled(e.target.checked)}
                       style={{ accentColor: '#00C389' }} />
                Personalización
              </label>
              <div style={{ width: '1px', height: '24px', background: '#21262D' }} />
              <select
                value={selectedUser.id}
                onChange={(e) => handleUserChange(e.target.value)}
                style={{
                  padding: '6px 12px', borderRadius: '12px', background: '#161B22',
                  border: '1px solid #21262D', fontSize: '12px', color: '#E2E8F0',
                  cursor: 'pointer', fontFamily: 'Inter, sans-serif'
                }}>
                {users?.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
              </select>
            </>
          )}
        </div>
      </header>

      {/* ── VISTA CHAT ────────────────────── */}
      {activeView === 'chat' && (
        <main style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

          {/* Ficha Sidebar izquierda */}
          {personalizationEnabled && (
            <div style={{ width: '240px', flexShrink: 0, overflowY: 'auto',
                          borderRight: '1px solid #21262D', background: '#161B22' }}>
              <FichaSidebar ficha={ficha} visible={personalizationEnabled} user={selectedUser} />
            </div>
          )}

          {/* Chat central */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column',
                        overflow: 'hidden', borderRight: '1px solid #21262D' }}>
            <ChatPanel
              user={selectedUser}
              messages={messages}
              isStreaming={isStreaming}
              onSendMessage={handleSend}
              speech={{}}
            />
          </div>

          {/* Trace Panel derecha */}
          <div style={{ width: '340px', flexShrink: 0, overflowY: 'auto',
                        borderLeft: '1px solid #21262D', background: '#161B22' }}>
            <TracePanel trace={currentTrace} isStreaming={isStreaming} profile={profile} />
          </div>

        </main>
      )}

      {/* ── VISTA OBSERVABILIDAD ──────────── */}
      {activeView === 'obs' && <ObsDashboard />}

      {/* ── FOOTER ────────────────────── */}
      <footer style={{
        height: '32px', flexShrink: 0, display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', padding: '0 16px',
        background: '#0D1117', borderTop: '1px solid #21262D',
        fontSize: '10.5px', color: '#6B7280'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontFamily: 'monospace' }}>datathon · 2026</span>
          <div style={{ width: '2px', height: '2px', borderRadius: '50%', background: '#21262D' }} />
          <span>Havi v2.4.1</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#00C389' }} />
            <span>SSE conectado</span>
          </div>
          <div style={{ fontFamily: 'monospace' }}>/chat/stream</div>
        </div>
      </footer>

    </div>
  )
}
