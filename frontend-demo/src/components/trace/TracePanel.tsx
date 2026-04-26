import { useState } from 'react'
import { TraceSpan } from '../../types'
import { Code, ChevronRight } from 'lucide-react'
import { ConversationalProfile } from '../../hooks/useSSE'

interface TracePanelProps {
  trace: TraceSpan[]
  isStreaming?: boolean
  profile?: ConversationalProfile | null
}

const TONE_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  success: { bg: '#E6F9F3', color: '#00845C', border: '#A8EBD3' },
  warning: { bg: '#FFF3EB', color: '#C2570B', border: '#FFD4B0' },
  danger: { bg: '#FEF2F2', color: '#DC2626', border: '#FECACA' },
  info: { bg: '#EFF6FF', color: '#1D4ED8', border: '#BFDBFE' },
  purple: { bg: '#F0EDFF', color: '#5438D4', border: '#DDD5FF' },
  neutral: { bg: '#F3F4F6', color: '#4B5563', border: '#E5E7EB' },
}

const STATUS_BADGE: Record<string, { label: string; bg: string; color: string }> = {
  done: { label: 'done', bg: '#E6F9F3', color: '#00845C' },
  running: { label: 'running', bg: '#FFF3EB', color: '#C2570B' },
  error: { label: 'error', bg: '#FEF2F2', color: '#DC2626' },
  pending: { label: 'pending', bg: '#F3F4F6', color: '#9CA3AF' },
}

const NODE_CONFIG: Record<string, { icon: string; tone: string; label: string }> = {
  ficha_injector: { icon: 'FIC', tone: 'success', label: 'Ficha Injector' },
  guardrail_check: { icon: 'GRD', tone: 'warning', label: 'Guardrail' },
  profiler: { icon: 'PRF', tone: 'info', label: 'Profiler' },
  plan_research: { icon: 'PRS', tone: 'purple', label: 'Plan Research' },
  gather_context: { icon: 'GTC', tone: 'info', label: 'Gather Context' },
  draft_response_gen: { icon: 'DRG', tone: 'purple', label: 'Draft Response' },
  tool_ops: { icon: 'OPS', tone: 'success', label: 'Tool Ops' },
  summarizer: { icon: 'SUM', tone: 'success', label: 'Summarizer' },
}

const TraceNode = ({ node, idx, defaultOpen = false }: { node: TraceSpan; idx: number; defaultOpen?: boolean }) => {
  const [open, setOpen] = useState(defaultOpen)
  const config = NODE_CONFIG[node.node] || { icon: 'UNK', tone: 'neutral', label: node.node }
  const tone = TONE_STYLES[config.tone] || TONE_STYLES.neutral
  const status = STATUS_BADGE[node.status] || STATUS_BADGE.pending

  return (
    <div style={{ animation: `traceNodeIn 220ms ease-out ${idx * 40}ms backwards` }}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-start gap-2.5 px-2.5 py-2 rounded-[10px] hover:bg-[#1C2128] transition-colors text-left"
      >
        <div
          className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-[13px] relative transition-transform"
          style={{
            background: tone.bg,
            color: tone.color,
            border: `1px solid ${tone.border}`,
          }}
        >
          {config.icon}
          {node.status === 'running' && (
            <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-[#FF8C42] border-2 border-white animate-pulse" />
          )}
        </div>
        <div className="flex-1 min-w-0 pt-0.5">
          <div className="flex items-center justify-between gap-2">
            <div className="text-[12.5px] font-medium text-[#E2E8F0] leading-tight truncate">{config.label}</div>
            {node.status === 'running' ? (
              <div className="flex items-center gap-1 shrink-0">
                <div className="w-3 h-3 rounded-full border-2 border-[#FF8C42] border-t-transparent animate-spin" />
              </div>
            ) : (
              <div className="text-[10.5px] font-mono font-medium text-[#00C389] shrink-0">
                {node.latency_ms}ms
              </div>
            )}
          </div>
          <div className="flex items-center gap-1.5 mt-1">
            <div
              className="inline-flex items-center h-[18px] px-1.5 rounded-full text-[9.5px] font-semibold uppercase tracking-wide"
              style={{ background: status.bg, color: status.color }}
            >
              {node.status === 'running' && <div className="w-1 h-1 rounded-full bg-current mr-1 animate-pulse" />}
              {status.label}
            </div>
            <div className="text-[10px] font-mono text-[#6B7280] truncate">{node.node}</div>
            <div className="ml-auto">
              <ChevronRight
                size={11}
                style={{
                  color: '#9CA3AF',
                  transform: open ? 'rotate(90deg)' : 'none',
                  transition: 'transform 180ms',
                }}
              />
            </div>
          </div>
        </div>
      </button>
      {open && node.metadata && Object.keys(node.metadata).length > 0 && (
        <div className="ml-[34px] mr-1 mb-1.5">
          <pre
            className="mt-2 p-2.5 rounded-lg overflow-x-auto text-[10.5px] leading-[1.55]"
            style={{
              background: '#0D1117',
              color: '#E2E8F0',
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            }}
          >
            <code>{JSON.stringify(node.metadata, null, 2)}</code>
          </pre>
        </div>
      )}
    </div>
  )
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
    <div className="space-y-2 mb-3">
      <div className="text-[10px] font-semibold uppercase tracking-widest text-[#8B949E] px-2">Perfil</div>
      <div className="flex flex-wrap gap-2 px-2">
        {badges.map((badge, i) => (
          <div
            key={i}
            className="inline-flex items-center px-2 py-1 rounded-full text-[9px] font-medium"
            style={{
              background: 'rgba(0, 195, 137, 0.15)',
              color: '#00C389',
              border: '1px solid rgba(0, 195, 137, 0.3)',
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
  const totalLatency = trace.reduce((s, n) => s + (n.latency_ms || 0), 0)
  const doneCount = trace.filter((n) => n.status === 'done').length

  return (
    <aside className="w-[300px] shrink-0 bg-[#161B22] border-r border-[#21262D] flex flex-col h-full">
      <style>{`
        @keyframes traceNodeIn {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-[#21262D]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div className="text-[11px] font-semibold uppercase tracking-widest text-[#8B949E]">Ejecución del agente</div>
          </div>
          <div className="flex items-center gap-1 text-[10px] font-mono text-[#6B7280]">
            <Code size={10} />
            <span>SSE</span>
          </div>
        </div>

        {trace.length > 0 ? (
          <div className="mt-2 flex items-center gap-3">
            <div className="flex items-center gap-1">
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{
                  background: isStreaming ? '#FF8C42' : '#00C389',
                  animation: isStreaming ? 'pulse 1.4s infinite' : 'none',
                }}
              />
              <span className="text-[10.5px] font-medium" style={{ color: isStreaming ? '#FF8C42' : '#00C389' }}>
                {isStreaming ? 'ejecutando' : 'completado'}
              </span>
            </div>
            <div className="text-[10.5px] font-mono text-[#6B7280]">
              {doneCount}/{trace.length} nodos · {totalLatency}ms
            </div>
          </div>
        ) : null}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {trace.length === 0 ? (
          <div className="px-3 py-12 text-center">
            <div className="w-10 h-10 mx-auto mb-3 rounded-xl flex items-center justify-center" style={{ background: '#21262D' }}>
              ✨
            </div>
            <div className="text-[12px] font-medium text-[#8B949E]">Esperando ejecución</div>
            <div className="text-[10.5px] text-[#6B7280] mt-1">Envía un mensaje para ver el flujo del agente.</div>
          </div>
        ) : (
          <div>
            <ProfileBadges profile={profile} />
            <div className="space-y-0.5">
              {trace.map((node, idx) => (
                <TraceNode key={idx} node={node} idx={idx} defaultOpen={idx === 0 && !isStreaming} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-[#21262D] flex items-center justify-between bg-[#161B22]">
        <div className="text-[10px] font-mono text-[#6B7280]">claude-haiku-4.5</div>
        <div className="flex items-center gap-1 text-[10px] font-mono text-[#6B7280]">
          <div className="w-1.5 h-1.5 rounded-full bg-[#00C389]" />
          guardrails on
        </div>
      </div>
    </aside>
  )
}
