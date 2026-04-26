import { useState, useEffect } from 'react'
import { TraceRow as HookTraceRow } from '../../hooks/useMetrics'

interface DisplayTraceRow {
  id: string
  hora: string
  usuario: string
  query: string
  status: string
  statusColor: string
  latencia: string
  costo: string
}

const STATUS_CONFIG: Record<string, string> = {
  'pasó guards': '#00C389',
  'plan creado': '#00C389',
  'Hey Pro sugerido': '#00C389',
  'ok': '#6B7280',
  'actividad atípica': '#FF8C42',
  'guardrail block': '#EF4444',
}

interface TracesTableProps {
  rows: HookTraceRow[]
}

export function TracesTable({ rows }: TracesTableProps) {
  const [isConnected, setIsConnected] = useState(true)

  // Convertir las rows del hook a formato de display
  const traces = rows.map((row, idx) => ({
    id: `${idx}-${row.timestamp}`,
    hora: row.timestamp,
    usuario: row.user_id,
    query: row.query,
    status: `${row.status_label === 'ok' ? '✓' : row.status_label.includes('atípica') ? '⚠' : row.status_label === 'guardrail block' ? '✗' : '✓'} ${row.status_label}`,
    statusColor: STATUS_CONFIG[row.status_label] || '#6B7280',
    latencia: `${row.latency_ms}ms`,
    costo: `$${row.estimated_cost.toFixed(3)}`,
  })) as DisplayTraceRow[]

  // Simular ping de conexión
  useEffect(() => {
    setIsConnected(true)
  }, [])

  return (
    <div
      className="rounded-xl border border-[#21262D] overflow-hidden"
      style={{ background: '#161B22' }}
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#21262D] flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <div
            className="w-2 h-2 rounded-full"
            style={{
              background: isConnected ? '#00C389' : '#6B7280',
              animation: isConnected ? 'livePulse 1.4s infinite' : 'none',
            }}
          />
          <span className="text-[10px] font-semibold uppercase tracking-widest text-[#E2E8F0]">
            ● ÚLTIMOS TRACES · STREAMING
          </span>
        </div>
        <span className="text-[10px] font-mono text-[#6B7280]">actualiza cada 2s</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-[280px] overflow-y-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-[#0D1117]">
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-wide text-[#6B7280]">
                HORA
              </th>
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-wide text-[#6B7280]">
                USUARIO
              </th>
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-wide text-[#6B7280]">
                QUERY
              </th>
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-wide text-[#6B7280]">
                STATUS
              </th>
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-wide text-[#6B7280]">
                LATENCIA
              </th>
              <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-wide text-[#6B7280]">
                COSTO
              </th>
            </tr>
          </thead>
          <tbody>
            {traces.map((trace, idx) => (
              <tr
                key={trace.id}
                className="border-t border-[#21262D] hover:bg-[#1C2128] transition-colors"
                style={{ animation: `rowSlideDown 300ms ease-out ${idx * 30}ms backwards` }}
              >
                <td className="px-5 py-3 text-[11px] font-mono text-[#6B7280]">{trace.hora}</td>
                <td className="px-5 py-3">
                  <span
                    className="text-[11px] font-medium px-2.5 py-1 rounded-full"
                    style={{ background: '#21262D', color: '#8B949E' }}
                  >
                    {trace.usuario}
                  </span>
                </td>
                <td className="px-5 py-3 text-[13px] text-[#E2E8F0] max-w-[300px] truncate">
                  {trace.query}
                </td>
                <td className="px-5 py-3 text-[12px] font-medium" style={{ color: trace.statusColor }}>
                  {trace.status}
                </td>
                <td className="px-5 py-3 text-[11px] font-mono text-[#00C389]">{trace.latencia}</td>
                <td className="px-5 py-3 text-[11px] font-mono text-[#6B7280]">{trace.costo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
