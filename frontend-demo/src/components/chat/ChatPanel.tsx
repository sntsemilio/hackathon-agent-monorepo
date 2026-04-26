import { useEffect, useRef, useState } from 'react'
import { ChatMessage, DemoUser } from '../../types'

interface ChatPanelProps {
  user: DemoUser
  messages: ChatMessage[]
  isStreaming: boolean
  onSendMessage: (msg: string) => void
  pendingToolCall?: any
  onConfirmToolCall?: any
  speech?: any
}

export function ChatPanel({
  user,
  messages,
  isStreaming,
  onSendMessage,
  speech
}: ChatPanelProps) {
  const [input, setInput] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isStreaming])

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim() || isStreaming) return
    onSendMessage(input.trim())
    setInput('')
  }

  const sampleQuestions = Array.isArray(user.sample_questions)
    ? user.sample_questions.map(q => typeof q === 'string' ? q : q.text)
    : []

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column',
                  background: '#0D1117', overflow: 'hidden', height: '100%' }}>

      {/* ── ESTADO VACÍO ──────────────────────── */}
      {messages.length === 0 && !isStreaming && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column',
                      alignItems: 'center', justifyContent: 'center',
                      padding: '32px 24px', gap: '24px', overflowY: 'auto' }}>

          {/* Avatar + saludo */}
          <div style={{ display: 'flex', flexDirection: 'column',
                        alignItems: 'center', gap: '12px', textAlign: 'center' }}>
            <div style={{
              width: '56px', height: '56px', borderRadius: '50%', fontSize: '24px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(0,195,137,0.1)', border: '2px solid rgba(0,195,137,0.4)',
              fontWeight: 'bold'
            }}>{user.avatar || user.name.charAt(0).toUpperCase()}</div>
            <div>
              <h2 style={{ color: '#E2E8F0', fontWeight: 700, fontSize: '24px',
                           letterSpacing: '-0.02em', margin: 0 }}>
                Hola, {user.name?.split(' ')[0]}
              </h2>
              <p style={{ color: '#6B7280', fontSize: '14px', margin: '6px 0 0' }}>
                ¿En qué te ayudo hoy?
              </p>
            </div>
          </div>

          {/* Grid de preguntas */}
          {sampleQuestions?.length > 0 && (
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr',
              gap: '8px', width: '100%', maxWidth: '520px'
            }}>
              {sampleQuestions.slice(0, 4).map((q: string, i: number) => (
                <button key={i} onClick={() => onSendMessage(q)} style={{
                  background: '#161B22', border: '1px solid #21262D',
                  borderRadius: '12px', padding: '12px 14px', cursor: 'pointer',
                  fontSize: '12px', color: '#8B949E', textAlign: 'left',
                  lineHeight: 1.4, transition: 'all 180ms', fontFamily: 'Inter, sans-serif'
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = '#00C389'
                  e.currentTarget.style.background = 'rgba(0,195,137,0.06)'
                  e.currentTarget.style.color = '#E2E8F0'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = '#21262D'
                  e.currentTarget.style.background = '#161B22'
                  e.currentTarget.style.color = '#8B949E'
                }}>
                  {q}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── LISTA DE MENSAJES ─────────────────── */}
      {(messages.length > 0 || isStreaming) && (
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px',
                      display: 'flex', flexDirection: 'column', gap: '12px' }}
             ref={scrollRef}>
          {messages.map((msg: ChatMessage, i: number) => (
            <div key={i} className="msg-in" style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{
                maxWidth: msg.role === 'user' ? '70%' : '80%',
                padding: '12px 16px', borderRadius: msg.role === 'user'
                  ? '18px 18px 4px 18px'
                  : '4px 18px 18px 18px',
                fontSize: '14px', lineHeight: 1.6, fontFamily: 'Inter, sans-serif',
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, #00C389, #00A074)'
                  : '#1C2128',
                color: msg.role === 'user' ? '#0D1117' : '#E2E8F0',
                border: msg.role === 'user' ? 'none' : '1px solid #21262D',
                boxShadow: msg.role === 'user'
                  ? '0 2px 10px rgba(0,195,137,0.25)'
                  : '0 2px 8px rgba(0,0,0,0.2)'
              }}>
                {msg.content}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isStreaming && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                padding: '14px 18px', borderRadius: '4px 18px 18px 18px',
                background: '#1C2128', border: '1px solid #21262D',
                display: 'flex', gap: '5px', alignItems: 'center'
              }}>
                {[0, 0.2, 0.4].map((delay, i) => (
                  <span key={i} style={{
                    width: '7px', height: '7px', borderRadius: '50%',
                    background: '#8B949E', display: 'inline-block',
                    animation: `dotPulse 1.2s ease-in-out ${delay}s infinite`
                  }} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── INPUT ─────────────────────────────── */}
      <div style={{
        padding: '12px 16px', borderTop: '1px solid #21262D', background: '#0D1117'
      }}>
        <div style={{
          display: 'flex', gap: '10px', alignItems: 'center',
          background: '#161B22', borderRadius: '14px', padding: '8px 8px 8px 16px',
          border: '1.5px solid #21262D', transition: 'border-color 200ms'
        }}
        onFocusCapture={e => e.currentTarget.style.borderColor = '#00C389'}
        onBlurCapture={e => e.currentTarget.style.borderColor = '#21262D'}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit()
              }
            }}
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: '#E2E8F0', fontSize: '14px', fontFamily: 'Inter, sans-serif'
            }}
            placeholder="Pregúntale a Havi..."
          />
          <button
            onClick={handleSubmit}
            style={{
              width: '36px', height: '36px', borderRadius: '10px', border: 'none',
              cursor: input.trim() && !isStreaming ? 'pointer' : 'default', flexShrink: 0,
              transition: 'all 180ms', display: 'flex', alignItems: 'center',
              justifyContent: 'center', background: '#00C389', color: '#0D1117',
              fontWeight: 'bold', fontSize: '18px', opacity: input.trim() && !isStreaming ? 1 : 0.5
            }}>
            ↑
          </button>
        </div>
      </div>

    </div>
  )
}
