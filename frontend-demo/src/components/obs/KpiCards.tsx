import { BackendMetrics } from '../../hooks/useMetrics'

interface KpiCardProps {
  title: string
  accent: string
  rows: { label: string; value: string; color?: string; sub?: string }[]
  loading: boolean
}

function KpiCard({ title, accent, rows, loading }: KpiCardProps) {
  return (
    <div style={{
      background: '#161B22', borderRadius: '14px', padding: '20px',
      border: '1px solid #21262D', borderTop: `2px solid ${accent}`,
      display: 'flex', flexDirection: 'column', gap: '14px', fontFamily: 'Inter, sans-serif'
    }}>
      <p style={{ color: accent, fontSize: '10px', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.1em', margin: 0 }}>
        {title} <span style={{ color: '#484F58', fontWeight: 400 }}>· HOY</span>
      </p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {rows.map((row, i) => (
          <div key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between',
                          alignItems: 'baseline', gap: '8px' }}>
              <span style={{ color: '#8B949E', fontSize: '12px' }}>{row.label}</span>
              {loading
                ? <div className="skeleton" style={{ width: '60px', height: '16px', borderRadius: '4px' }} />
                : <span style={{ color: row.color ?? '#E2E8F0', fontWeight: 700, fontSize: '14px' }}>
                    {row.value}
                  </span>
              }
            </div>
            {row.sub && <p style={{ color: '#484F58', fontSize: '10px', margin: '2px 0 0' }}>{row.sub}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}

export function KpiCards({ metrics, loading }: { metrics: BackendMetrics | null; loading: boolean }) {
  const total   = metrics?.requests_total ?? 0
  const success = Math.round((metrics?.success_rate ?? 0.963) * total)
  const failed  = total - success
  const tokens  = metrics?.token_usage_total ?? 0
  const tokensStr = tokens > 1000000 ? `${(tokens/1000000).toFixed(2)}M`
                  : tokens > 1000 ? `${(tokens/1000).toFixed(1)}K` : String(tokens)
  const cost = (tokens * 0.00000053).toFixed(2)
  const cqStr = metrics?.tokens_per_request
    ? `$${(metrics.tokens_per_request * 0.00000053).toFixed(4)}`
    : '$0.0076'
  const latStr = metrics?.avg_latency_ms
    ? `${(metrics.avg_latency_ms / 1000).toFixed(1)}s`
    : '—'

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
      <KpiCard title="Volumen" accent="#8B7CF8" loading={loading} rows={[
        { label: 'Queries totales', value: total.toLocaleString() },
        { label: 'Exitosas', value: `${success.toLocaleString()} ${Math.round((metrics?.success_rate??0.963)*100)}%`, color: '#00C389' },
        { label: 'Fallidas', value: failed.toLocaleString(), color: '#EF4444' },
        { label: 'Latencia P95', value: latStr },
      ]} />
      <KpiCard title="Costos" accent="#6B7280" loading={loading} rows={[
        { label: 'Tokens procesados', value: tokensStr },
        { label: 'Costo LiteLLM', value: `$${cost}` },
        { label: 'Costo / query', value: cqStr },
        { label: 'vs call center', value: '-97%', color: '#00C389',
          sub: '$15 → $0.40 por retención' },
      ]} />
      <KpiCard title="Impacto" accent="#00C389" loading={loading} rows={[
        { label: 'Ingresos nuevos', value: '$45.2K', color: '#00C389' },
        { label: 'Clientes retenidos', value: '34' },
        { label: 'LTV adicional', value: '$238K' },
        { label: 'Fraude prevenido', value: '$120K', color: '#EF4444' },
      ]} />
      <KpiCard title="Seguridad" accent="#EF4444" loading={loading} rows={[
        { label: 'Alertas fraude', value: '89' },
        { label: 'Confirmadas', value: '87  98%', color: '#00C389' },
        { label: 'Falsos positivos', value: '2', sub: '0.02% del total' },
        { label: 'Cumplimiento AML/KYC', value: '100%', color: '#00C389' },
      ]} />
    </div>
  )
}
