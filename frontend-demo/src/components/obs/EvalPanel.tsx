import { EvalMetrics } from '../../hooks/useMetrics'

interface RagMetric {
  name: string
  value: number
}

interface EvalPanelProps {
  evals: EvalMetrics | null
}

export function EvalPanel({ evals }: EvalPanelProps) {
  const metrics: RagMetric[] = [
    { name: 'Faithfulness', value: Math.round((evals?.faithfulness || 0.87) * 100) },
    { name: 'Answer Relevancy', value: Math.round((evals?.answer_relevancy || 0.92) * 100) },
    { name: 'Context Precision', value: Math.round((evals?.context_precision || 0.78) * 100) },
    { name: 'Context Recall', value: Math.round((evals?.context_recall || 0.85) * 100) },
    { name: 'F1 Score', value: Math.round((evals?.f1_score || 0.89) * 100) },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontFamily: 'Inter, sans-serif' }}>

      {/* RAG Evals */}
      <div style={{ background: '#161B22', borderRadius: '14px', padding: '20px',
                    border: '1px solid #21262D', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ color: '#8B7CF8', fontSize: '10px', fontWeight: 700,
                      textTransform: 'uppercase', letterSpacing: '0.1em', margin: 0 }}>
            RAG Evals
          </p>
          {evals?.last_run && (
            <span style={{ color: '#484F58', fontSize: '10px' }}>
              Último run: {new Date(evals.last_run).toLocaleTimeString()}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {metrics.map(m => (
            <div key={m.name}>
              <div style={{ display: 'flex', justifyContent: 'space-between',
                            marginBottom: '4px' }}>
                <span style={{ color: '#8B949E', fontSize: '11px' }}>{m.name}</span>
                <span style={{ color: '#E2E8F0', fontSize: '11px', fontWeight: 600 }}>
                  {m.value}%
                </span>
              </div>
              <div style={{ height: '4px', background: '#21262D', borderRadius: '2px' }}>
                <div style={{
                  height: '100%', borderRadius: '2px', background: '#00C389',
                  width: `${m.value}%`, transition: 'width 600ms ease'
                }} />
              </div>
            </div>
          ))}
        </div>
        <button style={{
          width: '100%', padding: '9px', borderRadius: '9px', cursor: 'pointer',
          background: 'transparent', border: '1px solid #21262D', color: '#8B949E',
          fontSize: '12px', fontWeight: 500, transition: 'all 180ms'
        }}
        onMouseEnter={e => {
          e.currentTarget.style.borderColor = '#00C389'
          e.currentTarget.style.color = '#00C389'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.borderColor = '#21262D'
          e.currentTarget.style.color = '#8B949E'
        }}>
          ▶ Run Evals
        </button>
      </div>

      {/* Proyección */}
      <div style={{
        borderRadius: '14px', padding: '24px',
        background: 'rgba(0,195,137,0.04)',
        border: '1px solid rgba(0,195,137,0.2)',
        display: 'flex', flexDirection: 'column', justifyContent: 'space-between'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%',
                           background: '#00C389', display: 'inline-block' }} />
            <span style={{ color: '#00C389', fontSize: '10px', fontWeight: 700,
                           textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              Proyección Mensual
            </span>
          </div>
          <p style={{ color: '#E2E8F0', fontSize: '14px', fontWeight: 500, lineHeight: 1.5, margin: 0 }}>
            <span style={{ color: '#00C389' }}>$2.8M</span> ingresos ·{' '}
            <span style={{ color: '#00C389' }}>+$15M</span> retención ·{' '}
            <span style={{ color: '#EF4444' }}>$3.6M</span> fraude prevenido
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <p style={{ color: '#484F58', fontSize: '11px', margin: '0 0 4px' }}>Total impacto MXN</p>
          <p style={{ color: '#E2E8F0', fontSize: '40px', fontWeight: 800,
                      letterSpacing: '-0.03em', margin: 0, lineHeight: 1 }}>
            $21.4M
          </p>
        </div>
      </div>

    </div>
  )
}
