import { useState, useEffect } from 'react'
import { DemoUser, SampleQuestion } from '../types'

const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000'

interface BackendDemoUser {
  user_id: string
  name: string
  avatar: string
  description: string
  segment_labels: string[]
  sample_questions: string[]
}

/**
 * Transform backend user format to frontend DemoUser format
 */
function transformUser(backendUser: BackendDemoUser): DemoUser {
  return {
    id: backendUser.user_id,
    user_id: backendUser.user_id,
    name: backendUser.name,
    avatar: backendUser.avatar,
    description: backendUser.description,
    segment_labels: backendUser.segment_labels,
    segment: backendUser.segment_labels[0] || 'default',
    theme_color: '#00C389',
    sample_questions: backendUser.sample_questions.map(text => ({ text })),
    questions: backendUser.sample_questions.map(text => ({ text })),
  }
}

/**
 * Hook to load demo users from the backend /users API endpoint.
 * Falls back to hardcoded fallback data if the API is unavailable.
 */
export function useUsers() {
  const [users, setUsers] = useState<DemoUser[]>(FALLBACK_USERS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await fetch(`${API_BASE}/users`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data = await res.json()
        if (data.users && Array.isArray(data.users)) {
          const transformedUsers = data.users.map(transformUser)
          setUsers(transformedUsers)
          setError(null)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load users')
        setUsers(FALLBACK_USERS)
      } finally {
        setLoading(false)
      }
    }

    fetchUsers()
  }, [])

  return { users, loading, error }
}

/**
 * Fallback demo users for when backend is unavailable.
 * Same data as backend/app/api/users.py DEMO_USERS, transformed to frontend format.
 */
const FALLBACK_USERS: DemoUser[] = [
  {
    user_id: 'USR-00001',
    name: 'Carla Mendoza',
    avatar: '👩‍💻',
    description: 'Actividad atípica · Presión financiera',
    segment: 'actividad_atipica_alerta',
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Por qué me bloquearon una transacción?' },
      { text: '¿Cómo puedo desbloquear mi tarjeta?' },
      { text: '¿Cuál es mi saldo actual?' },
      { text: '¿Mis datos están seguros?' },
    ],
  },
  {
    user_id: 'USR-00042',
    name: 'Javier López',
    avatar: '👨‍💼',
    description: 'Profesional · Inversor activo',
    segment: 'profesional_prospero_inversor',
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cuál es mi rendimiento en inversiones este mes?' },
      { text: '¿Qué productos de inversión me recomiendas?' },
      { text: '¿Cuál es el GAT real de mi cuenta?' },
      { text: '¿Puedo abrir un fondo indexado?' },
    ],
  },
  {
    user_id: 'USR-00108',
    name: 'Ana Torres',
    avatar: '👩‍🎓',
    description: 'Joven digital · Hey Pro',
    segment: 'joven_digital_hey_pro',
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cuánto cashback acumulé este mes?' },
      { text: '¿Qué hay de nuevo en Hey Shop?' },
      { text: '¿Cómo activo CoDi?' },
      { text: '¿Puedo subir mi límite de crédito?' },
    ],
  },
  {
    user_id: 'USR-00205',
    name: 'Roberto Sánchez',
    avatar: '👨‍🔧',
    description: 'Cliente estable · Perfil promedio',
    segment: 'cliente_promedio_estable',
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cuál es mi saldo?' },
      { text: '¿Puedo hacer una transferencia?' },
      { text: '¿Qué beneficios tengo con mi cuenta?' },
      { text: '¿Cómo activo Hey Pro?' },
    ],
  },
  {
    user_id: 'USR-00310',
    name: 'María González',
    avatar: '👩‍💼',
    description: 'Estrés financiero · Necesita apoyo',
    segment: 'usuario_estres_financiero',
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Puedo reestructurar mi deuda?' },
      { text: '¿Cuánto debo en total?' },
      { text: '¿Hay algún plan de pagos disponible?' },
      { text: '¿Puedo pausar un pago?' },
    ],
  },
  {
    user_id: 'USR-00415',
    name: 'Carlos Mendivil',
    avatar: '🧑‍💻',
    description: 'Usuario básico · Nuevo cliente',
    segment: 'usuario_basico_bajo_enganche',
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cómo funciona la cuenta Hey?' },
      { text: '¿Cómo deposito dinero?' },
      { text: '¿Hay comisiones?' },
      { text: '¿Puedo solicitar una tarjeta de crédito?' },
    ],
  },
  {
    user_id: 'USR-00520',
    name: 'Daniela Ruiz',
    avatar: '👩‍🎨',
    description: 'Empresaria · Alto volumen',
    segment: 'empresario_alto_volumen',
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cómo configuro nómina para mi empresa?' },
      { text: '¿Puedo facturar desde Hey?' },
      { text: '¿Hay crédito PYME disponible?' },
      { text: '¿Cómo muevo grandes volúmenes?' },
    ],
  },
  {
    user_id: 'USR-00630',
    name: 'Luis Fernández',
    avatar: '👨‍🌾',
    description: 'Ahorrador · Construcción crediticia',
    segment: 'en_construccion_crediticia',
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cómo mejoro mi score buró?' },
      { text: '¿Cuánto he ahorrado este mes?' },
      { text: '¿Me conviene una tarjeta garantizada?' },
      { text: '¿Cuál es mi historial de pagos?' },
    ],
  },
]
