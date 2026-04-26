import { useState } from "react"

interface LoginScreenProps {
  onEnter: () => void
}

export default function LoginScreen({ onEnter }: LoginScreenProps) {
  const [loading, setLoading] = useState(false)

  const handleEnter = () => {
    setLoading(true)
    setTimeout(onEnter, 1100)
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: '#0D1117',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, overflow: 'hidden'
    }}>
      {/* Grid sutil de fondo */}
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.04,
        backgroundImage: 'linear-gradient(#00C389 1px, transparent 1px), linear-gradient(90deg, #00C389 1px, transparent 1px)',
        backgroundSize: '48px 48px', pointerEvents: 'none'
      }} />

      {/* Glow central */}
      <div style={{
        position: 'absolute', width: '500px', height: '500px',
        borderRadius: '50%', opacity: 0.06, pointerEvents: 'none',
        background: 'radial-gradient(circle, #00C389, transparent 70%)'
      }} />

      {/* Card central */}
      <div style={{
        position: 'relative', display: 'flex', flexDirection: 'column',
        alignItems: 'center', gap: '32px', maxWidth: '340px', width: '100%',
        padding: '48px 32px'
      }}>

        {/* Logo */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
          <img src="/hey-banco-logo.svg" alt="Hey Banco"
               style={{ height: '56px', width: 'auto' }}
               onError={e => (e.currentTarget.style.display = 'none')} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              color: '#00C389', fontWeight: 800, fontSize: '28px',
              letterSpacing: '-0.03em', fontFamily: 'Inter, sans-serif'
            }}>havi</span>
            <span style={{
              background: 'rgba(0,195,137,0.15)', color: '#00C389',
              fontSize: '11px', padding: '3px 7px', borderRadius: '6px', fontWeight: 700
            }}>✦</span>
          </div>
          <span style={{
            color: '#484F58', fontSize: '11px', fontWeight: 600,
            letterSpacing: '0.12em', textTransform: 'uppercase'
          }}>
            by Hey Banco · Datathon 2026
          </span>
        </div>

        {/* Separador */}
        <div style={{ width: '48px', height: '1px', background: '#21262D' }} />

        {/* Descripción */}
        <p style={{
          color: '#8B949E', fontSize: '13px', textAlign: 'center', lineHeight: 1.6,
          margin: '-16px 0'
        }}>
          Asistente financiero inteligente con personalización por segmento de cliente.
        </p>

        {/* Botón — NO full width */}
        <button
          onClick={handleEnter}
          disabled={loading}
          style={{
            width: '240px', padding: '13px 0', borderRadius: '12px', border: 'none',
            cursor: loading ? 'default' : 'pointer', fontSize: '14px', fontWeight: 600,
            background: loading
              ? '#00A074'
              : 'linear-gradient(135deg, #00C389 0%, #00A074 100%)',
            color: '#0D1117',
            boxShadow: '0 4px 20px rgba(0,195,137,0.35)',
            transition: 'all 200ms',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
          }}
        >
          {loading ? (
            <>
              <svg style={{ animation: 'spin 0.8s linear infinite', width: 16, height: 16 }}
                   viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="rgba(13,17,23,0.3)" strokeWidth="3"/>
                <path d="M12 2a10 10 0 0 1 10 10" stroke="#0D1117" strokeWidth="3"
                      strokeLinecap="round"/>
              </svg>
              Iniciando...
            </>
          ) : 'Entrar al sistema'}
        </button>

        {/* Badge versión */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px',
                      color: '#484F58', fontSize: '11px' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%',
                         background: '#00C389', display: 'inline-block' }} />
          Demo local · v1.0 · Datathon 2026
        </div>
      </div>
    </div>
  )
}
