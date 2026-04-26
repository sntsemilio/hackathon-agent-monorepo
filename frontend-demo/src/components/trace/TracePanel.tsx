import { useRef, useEffect } from 'react'
import { Code, Sparkles } from 'lucide-react'
import { TraceNode } from './TraceNode'
import { TraceSpan } from '../../types'
import { ConversationalProfile } from '../../hooks/useSSE'

interface TracePanelProps {
  trace: TraceSpan[]
  isStreaming?: boolean
  profile?: ConversationalProfile | null
}

const ProfileBadges = ({ profile }: { profile: ConversationalProfile | null | undefined }) => {
  if (!profile) return null

  const badges = []
  if (profile.intent) badges.push({ label: 'intent', value: profile.intent.replace(/_/g, ' ') })
  if (profile.sentiment) badges.push({ label: 'sentiment', value: profile.sentiment })
  if (profile.urgency) badges.push({ label: 'urgency', value: profile.urgency })
  if (profile.topic) badges.push({ label: 'topic', value: profile.topic })

  if (badges.length === 0) return null

  return (
    <div style={{ marginBottom: 12 }}>
      <div
        className="text-[10px] font-semibold uppercase tracking-widest px-2"
        style={{ color: '#6B7280', marginBottom: 8 }}
      >
        Perfil
      </div>
      <div className="flex flex-wrap gap-2 px-2">
        {badges.map((badge, i) => (
          <div
            key={i}
            className="inline-flex items-center px-2 py-1 rounded-full text-[9px] font-medium"
            style={{
              background: 'rgba(0,195,137,0.12)',
              color: '#3FDDA8',
              border: '1px solid rgba(0,195,137,0.30)',
            }}
          >
            {badge.value}
          </div>
        ))}
      </div>
    </div>
  )
}

export function TracePanel({ trace, isStreaming, profile }: TracePanelProps) {
  const scrollerRef = useRef<HTMLDivElement>(null)
  const totalLatency = trace.reduce((s, n) => s + (n.latency_ms || 0), 0)
  const doneCount = trace.filter((n) => n.status === 'done').length

  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight
    }
  }, [trace, isStreaming])

  useEffect(() => {
    console.log('[trace]', trace)
  }, [trace])

  return (
    <aside
      className="w-[300px] shrink-0 flex flex-col h-full"
      style={{
        background: '#0D1117',
        borderRight: '1px solid #21262D',
        color: '#F0F6FC',
      }}
    >
      <style>{`
        @keyframes traceNodeIn {
          from { opacity: 0; transform: translateX(-8px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>

      {/* ── HEADER ────────────────────────────── */}
      <div
        className="px-4 pt-4 pb-3 border-b"
        style={{
          borderBottomColor: '#21262D',
        }}
      >
        <div className="flex items-center justify-between">
          <div
            className="text-[11px] font-semibold uppercase tracking-[0.08em]"
            style={{ color: '#C9D1D9' }}
          >
            Ejecución del agente
          </div>
          <div className="flex items-center gap-1 text-[10px] font-mono" style={{ color: '#6B7280' }}>
            <Code size={10} />
            <span>SSE</span>
          </div>
        </div>

        {trace.length > 0 && (
          <div className="flex items-center gap-3" style={{ marginTop: 8 }}>
            <div className="flex items-center gap-1">
              <div
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: isStreaming ? '#FF8C42' : '#00C389',
                  animation: isStreaming ? 'pulse 1.6s infinite' : 'none',
                }}
              />
              <span
                style={{
                  fontSize: 10.5,
                  fontWeight: 500,
                  color: isStreaming ? '#FFA869' : '#3FDDA8',
                }}
              >
                {isStreaming ? 'ejecutando' : 'completado'}
              </span>
            </div>
            <span className="font-mono" style={{ fontSize: 10.5, color: '#8B949E' }}>
              {doneCount}/{trace.length} nodos · {totalLatency}ms
            </span>
          </div>
        )}
      </div>

      {/* ── CONTENT ────────────────────────────── */}
      <div ref={scrollerRef} className="flex-1 overflow-y-auto px-2 py-2">
        {trace.length === 0 ? (
          <div style={{ padding: '48px 12px', textAlign: 'center' }}>
            <div
              className="w-10 h-10 mx-auto mb-3 rounded-xl flex items-center justify-center"
              style={{ background: '#161B22', border: '1px solid #21262D' }}
            >
              <Sparkles size={18} style={{ color: '#6B7280' }} />
            </div>
            <div style={{ fontSize: 12, fontWeight: 500, color: '#C9D1D9' }}>
              Esperando ejecución
            </div>
            <div style={{ fontSize: 10.5, color: '#6B7280', marginTop: 4 }}>
              Envía un mensaje para ver el flujo del agente.
            </div>
          </div>
        ) : (
          <div>
            <ProfileBadges profile={profile} />
            <div className="space-y-0.5">
              {trace.map((node, idx) => (
                <TraceNode
                  key={`${node.node}-${idx}`}
                  node={node}
                  idx={idx}
                  defaultOpen={idx === 0 && !isStreaming}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── FOOTER ────────────────────────────── */}
      <div
        className="px-4 py-2.5 border-t flex items-center justify-between"
        style={{
          borderTopColor: '#21262D',
        }}
      >
        <div className="text-[10px] font-mono" style={{ color: '#6B7280' }}>
          claude-haiku-4.5
        </div>
        <div className="flex items-center gap-1 text-[10px] font-mono" style={{ color: '#6B7280' }}>
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              background: '#00C389',
            }}
          />
          guardrails on
        </div>
      </div>
    </aside>
  )
}
