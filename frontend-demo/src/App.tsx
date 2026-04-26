import { useState, useMemo, useEffect } from 'react'
import { useSSE } from './hooks/useSSE'
import { useUsers } from './hooks/useUsers'
import { ChatPanel } from './components/chat/ChatPanel'
import { FichaSidebar } from './components/ficha/FichaSidebar'
import { TracePanel } from './components/trace/TracePanel'
import { ObsDashboard } from './components/obs/ObsDashboard'
import LoginScreen from './components/login/LoginScreen'
import { DemoUser, Ficha } from './types'

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [selectedUserIdx, setSelectedUserIdx] = useState(0)
  const [personalizationEnabled, setPersonalizationEnabled] = useState(true)
  const [activeView, setActiveView] = useState<'chat' | 'obs'>('chat')
  const [mockFicha, setMockFicha] = useState<Ficha | null>(null)

  const { messages, currentTrace, ficha: sseficha, profile, isStreaming, sendMessage, clearMessages } = useSSE()
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

  // Prioriza la ficha real del SSE, si no está disponible usa la mock
  const ficha = sseficha || mockFicha

  const handleSend = (message: string) => {
    sendMessage(message, personalizationEnabled ? selectedUser?.user_id : null)
  }

  const handleUserChange = (userId: string) => {
    const idx = users?.findIndex((u) => u.id === userId) ?? 0
    setSelectedUserIdx(idx)
    clearMessages()
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
