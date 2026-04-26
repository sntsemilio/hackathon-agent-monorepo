import { useMetrics } from '../../hooks/useMetrics'
import { KpiCards } from './KpiCards'
import { TracesTable } from './TracesTable'
import { EvalPanel } from './EvalPanel'

export function ObsDashboard() {
  const { metrics, evals, loading, lastUpdated, refresh } = useMetrics(2000)

  return (
    <main className="flex-1 flex flex-col min-h-0 bg-[#0D1117]">
      <style>{`
        @keyframes rowSlideDown {
          from {
            opacity: 0;
            transform: translateY(-12px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes livePulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>

      {/* Title Strip */}
      <div className="px-6 py-5 border-b border-[#21262D]">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-widest text-[#00C389]">
            <span>●</span>
            <span>OBSERVABILIDAD</span>
          </div>
          {lastUpdated && (
            <span className="text-[10px] text-[#484F58] ml-auto">
              actualizado {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={refresh}
            className="text-[10px] text-[#8B949E] hover:text-[#00C389] transition-colors px-2 py-1 rounded border border-[#21262D] hover:border-[#00C389]"
          >
            ↻ Refresh
          </button>
        </div>
        <div className="flex items-baseline gap-2 mt-2">
          <h1 className="text-[32px] font-bold text-white tracking-tight">Dashboard en vivo</h1>
          <span className="text-[14px] font-medium text-[#6B7280]">·</span>
          <span className="text-[14px] font-medium text-[#6B7280]">data-driven, sin sorpresas.</span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="px-6 py-6 space-y-6">
          {/* KPI Cards */}
          <KpiCards metrics={metrics} loading={loading} />

          {/* Traces Table */}
          <TracesTable rows={metrics?.latest_trace ?? []} />

          {/* RAG Evals + Proyección */}
          <EvalPanel evals={evals} />
        </div>
      </div>
    </main>
  )
}
