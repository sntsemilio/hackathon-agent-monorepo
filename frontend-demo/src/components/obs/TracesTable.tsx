import { TraceRow } from '../../hooks/useMetrics'

const STATUS_COLOR: Record<string, string> = {
  'pasó guards': '#00C389',
  'plan creado': '#00C389',
  'Hey Pro sugerido': '#00C389',
  'ok': '#6B7280',
  'actividad atípica': '#FF8C42',
  'guardrail block': '#EF4444',
}

function statusColor(s: string) {
  if (!s) return '#6B7280'
  if (s.includes('atípica') || s.includes('alerta') || s.includes('warning')) return '#FF8C42'
  if (s.includes('block') || s.includes('error') || s.includes('fail')) return '#EF4444'
  return '#00C389'
}

const DEMO_ROWS: TraceRow[] = [
  { timestamp: '03:47:12', user_id: 'USR-00415', query: 'Transferencia $100K · cuenta nueva', status_label: 'pasó guards', latency_ms: 967, estimated_cost: 0.006 },
  { timestamp: '03:45:48', user_id: 'USR-00108', query: 'Reestructura de deuda', status_label: 'plan creado', latency_ms: 617, estimated_cost: 0.005 },
  { timestamp: '03:42:03', user_id: 'USR-00001', query: 'Inversiones — empezar con poco', status_label: 'Hey Pro sugerido', latency_ms: 549, estimated_cost: 0.004 },
  { timestamp: '03:40:51', user_id: 'USR-08821', query: 'Consulta de balance', status_label: 'ok', latency_ms: 423, estimated_cost: 0.003 },
]

export function TracesTable({ rows }: { rows: TraceRow[] }) {
  const data = rows?.length > 0 ? rows : DEMO_ROWS

  const th = { color: '#484F58', fontSize: '10px', fontWeight: 700,
               textTransform: 'uppercase' as const, letterSpacing: '0.08em',
               padding: '8px 12px', textAlign: 'left' as const, fontFamily: 'Inter, sans-serif' }
  const td = { padding: '10px 12px', fontSize: '12px', fontFamily: 'Inter, sans-serif' }

  return (
    <div style={{ background: '#161B22', borderRadius: '14px',
                  border: '1px solid #21262D', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '14px 16px', borderBottom: '1px solid #21262D',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%',
                         background: '#00C389', display: 'inline-block',
                         animation: 'livePulse 2s ease-in-out infinite' }} />
          <span style={{ color: '#E2E8F0', fontSize: '11px', fontWeight: 700,
                         textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Últimos Traces · Streaming
          </span>
        </div>
        <span style={{ color: '#484F58', fontSize: '10px' }}>actualiza cada 2s</span>
      </div>

      {/* Tabla */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #21262D' }}>
              {['Hora','Usuario','Query','Status','Latencia','Costo'].map(h => (
                <th key={h} style={th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row: TraceRow, i: number) => (
              <tr key={i} className="row-in"
                  style={{ borderBottom: '1px solid rgba(33,38,45,0.6)',
                           transition: 'background 150ms' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.025)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ ...td, fontFamily: 'monospace', color: '#6B7280' }}>{row.timestamp}</td>
                <td style={td}>
                  <span style={{ background: '#21262D', color: '#8B949E', fontSize: '11px',
                                 padding: '2px 7px', borderRadius: '5px', fontFamily: 'monospace' }}>
                    {row.user_id}
                  </span>
                </td>
                <td style={{ ...td, color: '#E2E8F0', maxWidth: '280px' }}>
                  <span style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis',
                                 whiteSpace: 'nowrap' }}>{row.query}</span>
                </td>
                <td style={td}>
                  <span style={{ color: statusColor(row.status_label), fontWeight: 500 }}>
                    ✓ {row.status_label}
                  </span>
                </td>
                <td style={{ ...td, fontFamily: 'monospace', color: '#00C389' }}>
                  {row.latency_ms}ms
                </td>
                <td style={{ ...td, fontFamily: 'monospace', color: '#6B7280' }}>
                  ${typeof row.estimated_cost === 'number' ? row.estimated_cost.toFixed(3) : row.estimated_cost}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
