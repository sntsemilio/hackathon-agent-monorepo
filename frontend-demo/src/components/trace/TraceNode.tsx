import { useState } from 'react'
import { ChevronRight } from 'lucide-react'
import { TraceNodeIcon } from './TraceNodeIcon'
import { TraceStatusBadge } from './TraceStatusBadge'
import { JsonView } from './JsonView'
import { NODE_LABELS } from './tokens'
import { TraceSpan } from '../../types'

interface TraceNodeProps {
  node: TraceSpan
  idx: number
  defaultOpen?: boolean
}

const Spinner = () => (
  <div
    style={{
      width: 12,
      height: 12,
      borderRadius: '50%',
      border: '2px solid #FF8C42',
      borderTopColor: 'transparent',
      animation: 'spin 0.8s linear infinite',
    }}
  />
)

export function TraceNode({ node, idx, defaultOpen = false }: TraceNodeProps) {
  const [open, setOpen] = useState(defaultOpen)
  const label = NODE_LABELS[node.node] ?? node.node
  const hasMetadata = node.metadata && Object.keys(node.metadata).length > 0

  return (
    <div
      style={{
        animation: `traceNodeIn 220ms ease-out ${idx * 40}ms backwards`,
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls={`trace-${node.node}-${idx}`}
        className="w-full flex items-start gap-2.5 rounded-[10px] text-left transition-colors"
        style={{
          padding: '8px 10px',
          background: open ? '#1C2128' : '#161B22',
          border: '1px solid #21262D',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = '#1C2128')}
        onMouseLeave={(e) => (e.currentTarget.style.background = open ? '#1C2128' : '#161B22')}
      >
        <TraceNodeIcon node={node.node} status={node.status} />

        <div className="flex-1 min-w-0" style={{ paddingTop: 2 }}>
          {/* Label line */}
          <div className="flex items-center justify-between gap-2">
            <span
              className="truncate"
              style={{ fontSize: 12.5, fontWeight: 500, color: '#F0F6FC' }}
            >
              {label}
            </span>
            {node.status === 'running' ? (
              <Spinner />
            ) : (
              <span
                className="font-mono shrink-0"
                style={{ fontSize: 10.5, fontWeight: 500, color: '#3FDDA8' }}
              >
                {node.latency_ms ?? 0}ms
              </span>
            )}
          </div>

          {/* Status line */}
          <div className="flex items-center gap-1.5" style={{ marginTop: 4 }}>
            <TraceStatusBadge status={node.status} />
            <span
              className="font-mono truncate"
              style={{ fontSize: 10, color: '#6B7280' }}
            >
              {node.node}
            </span>
            <ChevronRight
              size={11}
              style={{
                color: '#6B7280',
                marginLeft: 'auto',
                transform: open ? 'rotate(90deg)' : 'none',
                transition: 'transform 180ms',
              }}
            />
          </div>
        </div>
      </button>

      {/* JSON expandible */}
      {open && hasMetadata && (
        <div
          id={`trace-${node.node}-${idx}`}
          style={{ marginLeft: 34, marginRight: 4, marginBottom: 6 }}
        >
          <JsonView data={node.metadata} />
        </div>
      )}
    </div>
  )
}
