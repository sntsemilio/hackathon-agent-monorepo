import { useState } from "react"
import { motion } from "framer-motion"

interface LoginScreenProps {
  onEnter: () => void
}

export default function LoginScreen({ onEnter }: LoginScreenProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleEnter = () => {
    setIsLoading(true)
    // Simula una verificación de 1.2 segundos antes de entrar
    setTimeout(() => onEnter(), 1200)
  }

  return (
    <div className="min-h-screen bg-[#0D1117] flex items-center justify-center relative overflow-hidden">

      {/* Fondo con grid sutil */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: 'linear-gradient(#00C389 1px, transparent 1px), linear-gradient(90deg, #00C389 1px, transparent 1px)',
        backgroundSize: '40px 40px'
      }}/>

      {/* Glow verde sutil en el centro */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-96 h-96 rounded-full opacity-10" style={{
          background: 'radial-gradient(circle, #00C389, transparent 70%)'
        }}/>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
        className="relative z-10 flex flex-col items-center gap-8 max-w-sm w-full px-6"
      >
        {/* Logo */}
        <div className="flex flex-col items-center gap-3">
          <img
            src="/hey-banco-logo.svg"
            alt="Hey Banco"
            className="h-12 w-auto"
            onError={(e) => {
              // fallback inline si el SVG no carga
              (e.target as HTMLImageElement).style.display = 'none'
            }}
          />
          {/* Fallback texto si no hay SVG */}
          <span className="text-3xl font-extrabold tracking-tight" style={{ color: '#00C389' }}>
            havi
          </span>
          <span className="text-xs font-semibold tracking-[0.15em] uppercase"
                style={{ color: '#484F58' }}>
            by hey banco · datathon 2026
          </span>
        </div>

        {/* Separador */}
        <div className="w-16 h-px" style={{ background: '#21262D' }}/>

        {/* Descripción */}
        <div className="text-center">
          <p className="text-sm leading-relaxed" style={{ color: '#8B949E' }}>
            Asistente financiero inteligente con personalización por segmento de cliente.
          </p>
        </div>

        {/* Botón de entrada */}
        <button
          onClick={handleEnter}
          disabled={isLoading}
          className="w-full py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-200 relative overflow-hidden"
          style={{
            background: isLoading ? '#00A074' : '#00C389',
            color: '#0D1117',
            boxShadow: '0 4px 14px rgba(0,195,137,0.30)'
          }}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10"
                        stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              Iniciando sesión...
            </span>
          ) : (
            "Entrar al sistema"
          )}
        </button>

        {/* Badge versión */}
        <div className="flex items-center gap-2 text-xs" style={{ color: '#484F58' }}>
          <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#00C389' }}/>
          <span>Demo local · v1.0 · Datathon 2026</span>
        </div>
      </motion.div>
    </div>
  )
}
