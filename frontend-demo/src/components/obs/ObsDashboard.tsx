import { useMetrics } from '../../hooks/useMetrics'
import { KpiCards } from './KpiCards'
import { TracesTable } from './TracesTable'
import { EvalPanel } from './EvalPanel'

export function ObsDashboard() {
  const { metrics, evals, loading, lastUpdated, refresh } = useMetrics(2000)

  return (
    <div style={{ flex: 1, overflowY: 'auto', background: '#0D1117',
                  padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', fontFamily: 'Inter, sans-serif' }}>

      {/* Title strip */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%',
                         background: '#00C389', display: 'inline-block',
                         animation: 'livePulse 2s ease-in-out infinite' }} />
          <span style={{ color: '#00C389', fontSize: '10px', fontWeight: 700,
                         textTransform: 'uppercase', letterSpacing: '0.12em' }}>
            Observabilidad
          </span>
          {lastUpdated && (
            <span style={{ color: '#484F58', fontSize: '10px', marginLeft: 'auto' }}>
              actualizado {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button onClick={refresh} style={{
            color: '#8B949E', fontSize: '11px', background: 'transparent',
            border: '1px solid #21262D', borderRadius: '6px', padding: '3px 10px',
            cursor: 'pointer', fontFamily: 'Inter, sans-serif'
          }}>↻ Refresh</button>
        </div>
        <h1 style={{ margin: 0, fontSize: '30px', fontWeight: 800, lineHeight: 1.1 }}>
          <span style={{ color: '#E2E8F0' }}>Dashboard en vivo · </span>
          <span style={{ color: '#4B5563' }}>data-driven, sin sorpresas.</span>
        </h1>
      </div>

      {/* KPI Cards */}
      <KpiCards metrics={metrics} loading={loading} />

      {/* Traces Table */}
      <TracesTable rows={metrics?.latest_trace ?? []} />

      {/* Evals + Proyección */}
      <EvalPanel evals={evals} />

    </div>
  )
}
