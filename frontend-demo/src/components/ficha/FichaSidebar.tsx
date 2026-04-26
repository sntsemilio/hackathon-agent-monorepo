import { DemoUser, Ficha } from '../../types'

interface FichaSidebarProps {
  user: DemoUser | null
  ficha: Ficha | null
  visible: boolean
}

function getInitials(text: string): string {
  if (!text) return '?'
  return text.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

export function FichaSidebar({ user, ficha, visible }: FichaSidebarProps) {

  if (!visible || !user) return null

  if (!ficha) return (
    <div style={{ padding: '20px', textAlign: 'center', color: '#484F58', fontSize: '12px', fontFamily: 'Inter, sans-serif' }}>
      Cargando perfil...
    </div>
  )

  const riskColor = ficha?.risk_level === 'high' ? '#EF4444'
                  : ficha?.risk_level === 'medium' ? '#FF8C42'
                  : '#00C389'

  const card = (accentColor: string, label: string, name: string,
                sub?: string, extra?: React.ReactNode) => (
    <div style={{
      background: '#1C2128', borderRadius: '12px', padding: '12px',
      border: '1px solid #21262D', borderLeft: `3px solid ${accentColor}`, fontFamily: 'Inter, sans-serif'
    }}>
      <p style={{ color: accentColor, fontSize: '9px', fontWeight: 700,
                  textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '5px' }}>
        {label}
      </p>
      <p style={{ color: '#E2E8F0', fontSize: '12px', fontWeight: 600,
                  lineHeight: 1.3, marginBottom: sub ? '4px' : 0 }}>
        {name ? name.replace(/_/g, ' ') : '—'}
      </p>
      {sub && <p style={{ color: '#8B949E', fontSize: '10px' }}>{sub}</p>}
      {extra}
    </div>
  )

  const userInitials = getInitials(user.name)

  return (
    <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>

      {/* Header */}
      <div style={{ paddingBottom: '10px', borderBottom: '1px solid #21262D',
                    display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'Inter, sans-serif' }}>
        <div style={{
          width: '32px', height: '32px', borderRadius: '50%',
          background: 'rgba(0,195,137,0.12)', border: '1.5px solid rgba(0,195,137,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px',
          fontWeight: 700, color: '#00C389', fontFamily: 'monospace'
        }}>{userInitials}</div>
        <div>
          <p style={{ color: '#E2E8F0', fontSize: '12px', fontWeight: 600, margin: 0 }}>
            {user.user_id ?? '—'}
          </p>
          <p style={{ color: '#8B949E', fontSize: '10px', margin: '2px 0 0' }}>Perfil activo</p>
        </div>
      </div>

      {/* Conductual */}
      {card('#6B4EFF', 'Conductual',
            ficha?.offer_strategy ?? 'Análisis en curso',
            undefined)}

      {/* Transaccional */}
      {card('#00C389', 'Transaccional',
            `${ficha?.gasto ?? 0} MXN/mes`,
            undefined,
            ficha?.top_categories && ficha.top_categories.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
                {ficha.top_categories.slice(0, 3).map((c: string) => (
                  <span key={c} style={{
                    fontSize: '9px', padding: '2px 6px', borderRadius: '5px',
                    background: 'rgba(0,195,137,0.12)', color: '#00C389'
                  }}>{c}</span>
                ))}
              </div>
            ) : undefined
      )}

      {/* Salud Financiera */}
      {card(riskColor, 'Salud Financiera',
            `Score ${ficha?.health_score ?? 0}`,
            undefined,
            ficha?.risk_level === 'high' ? (
              <span style={{
                display: 'inline-block', marginTop: '6px', fontSize: '9px',
                padding: '2px 7px', borderRadius: '5px',
                background: 'rgba(239,68,68,0.12)', color: '#EF4444'
              }}>Riesgo alto</span>
            ) : undefined
      )}

    </div>
  )
}
