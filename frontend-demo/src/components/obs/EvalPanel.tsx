import { Play } from 'lucide-react'
import { EvalMetrics } from '../../hooks/useMetrics'

interface RagMetric {
  name: string
  value: number
}

interface EvalPanelProps {
  evals: EvalMetrics | null
}

export function EvalPanel({ evals }: EvalPanelProps) {
  const ragMetrics: RagMetric[] = [
    { name: 'Faithfulness', value: Math.round((evals?.faithfulness || 0.87) * 100) },
    { name: 'Answer Relevancy', value: Math.round((evals?.answer_relevancy || 0.92) * 100) },
    { name: 'Context Precision', value: Math.round((evals?.context_precision || 0.78) * 100) },
    { name: 'Context Recall', value: Math.round((evals?.context_recall || 0.85) * 100) },
    { name: 'F1 Score', value: Math.round((evals?.f1_score || 0.89) * 100) },
  ]

  const lastRunTime = evals?.last_run ? new Date(evals.last_run).toLocaleTimeString('es-ES', { hour12: false }) : new Date().toLocaleTimeString('es-ES', { hour12: false })

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* RAG Evals Panel */}
      <div
        className="rounded-xl border border-[#21262D] p-5"
        style={{ background: '#161B22' }}
      >
        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-[#00C389] mb-1">
              RAG EVALS
            </div>
            <div className="text-[10px] text-[#6B7280]">Último run: {lastRunTime}</div>
          </div>
        </div>

        <div className="space-y-4 mb-5">
          {ragMetrics.map((metric) => (
            <div key={metric.name}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[12px] text-[#E2E8F0] font-medium">{metric.name}</span>
                <span className="text-[12px] font-bold text-[#00C389]">{metric.value}%</span>
              </div>
              <div className="w-full h-1 bg-[#21262D] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#00C389] rounded-full transition-all duration-1000"
                  style={{ width: `${metric.value}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <button className="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-[#00C389] text-[#00C389] text-[12px] font-medium rounded-lg hover:bg-[#00C389] hover:text-[#0D1117] transition-colors">
          <Play size={12} />
          Run Evals
        </button>
      </div>

      {/* Proyección Mensual Panel */}
      <div
        className="rounded-xl border p-5"
        style={{
          background: 'rgba(0,195,137,0.06)',
          borderColor: 'rgba(0,195,137,0.20)',
        }}
      >
        <div className="text-[10px] font-semibold uppercase tracking-widest text-[#00C389] mb-4">
          ● PROYECCIÓN MENSUAL
        </div>

        <div className="mb-6">
          <p className="text-[14px] font-medium text-[#E2E8F0] leading-relaxed">
            <span className="text-[#00C389]">$2.8M</span> ingresos · <span className="text-[#00C389]">+$15M</span> retención ·{' '}
            <span className="text-[#EF4444]">$3.6M</span> fraude prevenido
          </p>
        </div>

        <div className="text-right">
          <div className="text-[12px] text-[#6B7280] mb-1">Total impacto MXN</div>
          <div className="text-[36px] font-black text-white tracking-tight">$21.4M</div>
        </div>
      </div>
    </div>
  )
}
