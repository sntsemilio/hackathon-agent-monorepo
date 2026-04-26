import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, MessageCircle, BarChart3 } from 'lucide-react'
import { useSSE } from './hooks/useSSE'
import { useUsers } from './hooks/useUsers'
import { ChatPanel } from './components/chat/ChatPanel'
import { FichaSidebar } from './components/ficha/FichaSidebar'
import { TracePanel } from './components/trace/TracePanel'
import { ObsDashboard } from './components/obs/ObsDashboard'
import { NotificationToast } from './components/notifications/NotificationToast'
import LoginScreen from './components/login/LoginScreen'

interface DemoUser {
  id: string
  name: string
  user_id: string
  avatar: string
  segment_labels: string[]
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [selectedUserIdx, setSelectedUserIdx] = useState(0)
  const [personalizationEnabled, setPersonalizationEnabled] = useState(true)
  const [activeView, setActiveView] = useState<'chat' | 'obs'>('chat')

  const { messages, currentTrace, ficha, profile, isStreaming, sendMessage, clearMessages } = useSSE()
  const { users } = useUsers()

  const selectedUser = useMemo(
    () => (users?.[selectedUserIdx] as DemoUser) || null,
    [users, selectedUserIdx]
  )

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
    return <div className="flex items-center justify-center h-screen bg-[#0D1117]">Loading...</div>
  }

  const mockSpeech = {
    transcript: '',
    isListening: false,
    startListening: () => {},
    stopListening: () => {}
  }

  return (
    <div className="min-h-screen bg-[#0D1117] flex flex-col font-sans overflow-hidden">
      {/* Header */}
      <header className="h-14 px-5 flex items-center justify-between bg-[#0D1117] border-b border-[#21262D] shrink-0" style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.30)' }}>
        <div className="flex items-center gap-6">
          {/* Logo & Branding */}
          <div className="flex items-center gap-2 select-none">
            <img
              src="/hey-banco-logo.svg"
              alt="Hey Banco"
              className="h-5 w-auto object-contain"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
            <div className="flex items-baseline gap-1.5">
              <span className="font-extrabold text-[15px] tracking-tighter text-white">havi</span>
              <span className="text-[#00C389] text-xs font-bold px-1 py-0.5 rounded" style={{ background: 'rgba(0,195,137,0.15)' }}>
                ✦
              </span>
            </div>
            {/* Separator */}
            <div className="w-px h-5 bg-[#21262D] ml-1" />
          </div>

          {/* Nav Tabs */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setActiveView('chat')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 text-[12px] font-medium transition-all duration-200`}
              style={{
                borderRadius: '8px',
                background: activeView === 'chat' ? '#00C389' : 'transparent',
                color: activeView === 'chat' ? '#0D1117' : '#8B949E'
              }}
              onMouseEnter={(e) => {
                if (activeView !== 'chat') {
                  (e.currentTarget as HTMLElement).style.color = '#E2E8F0'
                }
              }}
              onMouseLeave={(e) => {
                if (activeView !== 'chat') {
                  (e.currentTarget as HTMLElement).style.color = '#8B949E'
                }
              }}
            >
              <MessageCircle size={13} />
              Chat
            </button>
            <button
              onClick={() => setActiveView('obs')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 text-[12px] font-medium transition-all duration-200`}
              style={{
                borderRadius: '8px',
                background: activeView === 'obs' ? '#00C389' : 'transparent',
                color: activeView === 'obs' ? '#0D1117' : '#8B949E'
              }}
              onMouseEnter={(e) => {
                if (activeView !== 'obs') {
                  (e.currentTarget as HTMLElement).style.color = '#E2E8F0'
                }
              }}
              onMouseLeave={(e) => {
                if (activeView !== 'obs') {
                  (e.currentTarget as HTMLElement).style.color = '#8B949E'
                }
              }}
            >
              <BarChart3 size={13} />
              Obs
            </button>
          </div>

          {/* Datathon Badge */}
          <div className="hidden md:flex items-center gap-1 h-7 px-2.5 rounded-full" style={{ background: 'rgba(0,195,137,0.10)', border: '1px solid rgba(0,195,137,0.30)' }}>
            <div className="w-1.5 h-1.5 rounded-full bg-[#00C389] animate-pulse" />
            <span className="text-[10.5px] font-semibold tracking-wider text-[#00C389]">DATATHON 2026</span>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4">
          {activeView === 'chat' && (
            <>
              <label className="flex items-center gap-2 text-sm text-[#8B949E] cursor-pointer">
                <input
                  type="checkbox"
                  checked={personalizationEnabled}
                  onChange={(e) => setPersonalizationEnabled(e.target.checked)}
                  className="w-4 h-4 rounded bg-[#161B22] border border-[#21262D] cursor-pointer"
                />
                Personalización
              </label>
              <div className="w-px h-6 bg-[#21262D]" />
              <select
                value={selectedUser.id}
                onChange={(e) => handleUserChange(e.target.value)}
                className="px-3 py-1.5 rounded-full bg-[#161B22] border border-[#21262D] text-[12px] text-[#E2E8F0] cursor-pointer hover:border-[#00C389] transition-colors"
              >
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

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <div className={`h-full grid gap-0 ${personalizationEnabled ? 'lg:grid-cols-[320px_1fr_340px]' : 'lg:grid-cols-[1fr_340px]'}`}>
          <AnimatePresence mode="wait">
            {activeView === 'chat' ? (
              <>
                {/* Left Column: Ficha Sidebar (visible when personalization ON) */}
                {personalizationEnabled && (
                  <FichaSidebar
                    user={selectedUser}
                    ficha={ficha}
                    visible={personalizationEnabled}
                  />
                )}

                {/* Center Column: Chat */}
                <motion.section
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="h-full flex flex-col overflow-hidden relative border-r border-[#21262D]"
                >
                  <ChatPanel
                    user={selectedUser}
                    messages={messages}
                    isStreaming={isStreaming}
                    onSendMessage={handleSend}
                    pendingToolCall={null}
                    onConfirmToolCall={() => {}}
                    speech={mockSpeech}
                  />
                </motion.section>

                {/* Right Column: Trace Panel */}
                <motion.aside
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                  className="border-l border-[#21262D] bg-[#0D1117] overflow-hidden hidden lg:block"
                >
                  <TracePanel trace={currentTrace} isStreaming={isStreaming} profile={profile} />
                </motion.aside>
              </>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="col-span-full h-full overflow-hidden"
              >
                <ObsDashboard />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="h-8 px-5 flex items-center justify-between bg-[#0D1117] border-t border-[#21262D] shrink-0 text-[10.5px] text-[#6B7280]">
        <div className="flex items-center gap-3">
          <span className="font-mono">datathon · 2026</span>
          <div className="w-0.5 h-0.5 rounded-full bg-[#21262D]" />
          <span>Havi v2.4.1</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[#00C389]" />
            <span>SSE conectado</span>
          </div>
          <div className="font-mono">/chat/stream</div>
        </div>
      </footer>
    </div>
  )
}
