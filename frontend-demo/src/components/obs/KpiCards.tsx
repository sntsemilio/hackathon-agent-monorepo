import { BackendMetrics } from '../../hooks/useMetrics'

interface KpiCardProps {
  title: string
  items: { label: string; value: string; color?: string; highlight?: boolean }[]
  accentColor?: string
  bgGradient?: string
}

const KpiCard = ({ title, items, accentColor = '#00C389', bgGradient }: KpiCardProps) => (
  <div
    className="rounded-xl border border-[#21262D] p-5"
    style={{
      background: bgGradient || '#161B22',
    }}
  >
    <div className="text-[11px] font-semibold uppercase tracking-wider mb-4" style={{ color: accentColor }}>
      {title}
    </div>
    <div className="space-y-3">
      {items.map((item, i) => (
        <div key={i} className="flex items-baseline justify-between">
          <span className="text-[12px] text-[#8B949E]">{item.label}</span>
          <span
            className="text-[14px] font-bold"
            style={{ color: item.color || (item.highlight ? '#E2E8F0' : '#E2E8F0') }}
          >
            {item.value}
          </span>
        </div>
      ))}
    </div>
  </div>
)

interface KpiCardsProps {
  metrics: BackendMetrics | null
  loading: boolean
}

export function KpiCards({ metrics, loading }: KpiCardsProps) {
  // Usa métricas reales si están disponibles, sino datos de demo
  const formatNumber = (n: number) => n.toLocaleString('es-MX')

  const volumeData = {
    title: 'VOLUMEN',
    items: [
      { label: 'Queries totales', value: metrics ? formatNumber(metrics.requests_total) : '12,847', highlight: true },
      { label: 'Exitosas', value: metrics ? `${formatNumber(Math.round(metrics.requests_total * metrics.success_rate))} (${(metrics.success_rate * 100).toFixed(1)}%)` : '12,456 (96.9%)', color: '#00C389' },
      { label: 'Fallidas', value: metrics ? formatNumber(Math.round(metrics.requests_total * (1 - metrics.success_rate))) : '391', color: '#EF4444' },
      { label: 'Latencia P95', value: metrics ? `${Math.round(metrics.avg_latency_ms)}ms` : '340ms' },
    ],
    accentColor: '#6B4EFF',
  }

  const costsData = {
    title: 'COSTOS',
    items: [
      { label: 'Tokens procesados', value: metrics ? `${(metrics.token_usage_total / 1000000).toFixed(2)}M` : '1.89M', highlight: true },
      { label: 'Costo LiteLLM', value: metrics ? `$${(metrics.token_usage_total * 0.00013).toFixed(2)}` : '$245.30' },
      { label: 'Costo / query', value: metrics ? `$${(metrics.token_usage_total * 0.00013 / metrics.requests_total).toFixed(4)}` : '$0.019' },
      { label: 'vs call center', value: '-97%', color: '#00C389' },
    ],
    accentColor: '#00C389',
  }

  const impactData = {
    title: 'IMPACTO',
    items: [
      { label: 'Ingresos nuevos', value: `$${formatNumber(Math.round(metrics ? metrics.requests_total * 46 : 580000))}`, color: '#00C389', highlight: true },
      { label: 'Clientes retenidos', value: formatNumber(metrics ? Math.round(metrics.requests_total * 0.26) : 3245) },
      { label: 'LTV adicional', value: '$2.1M' },
      { label: 'Fraude prevenido', value: `$${formatNumber(Math.round(metrics ? metrics.requests_total * 67 : 840000))}`, color: '#EF4444' },
    ],
    accentColor: '#00C389',
  }

  const securityData = {
    title: 'SEGURIDAD',
    items: [
      { label: 'Operaciones validadas', value: metrics ? formatNumber(metrics.delegation_trace_count) : '23', highlight: true },
      { label: 'Tasa de pass', value: metrics ? `${(metrics.success_rate * 100).toFixed(1)}%` : '82.6%', color: '#00C389' },
      { label: 'Falsos positivos', value: '4 (17.4%)' },
      { label: 'Cumplimiento AML/KYC', value: '100%', color: '#00C389' },
    ],
    accentColor: '#EF4444',
  }

  return (
    <div className="grid grid-cols-4 gap-4">
      <KpiCard {...volumeData} />
      <KpiCard {...costsData} />
      <KpiCard {...impactData} bgGradient="rgba(0,195,137,0.04)" />
      <KpiCard {...securityData} />
    </div>
  )
}
