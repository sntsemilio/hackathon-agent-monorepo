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
  // Look up ficha_mock from FALLBACK_USERS to preserve segmentation data
  const fallbackUser = FALLBACK_USERS.find(u => u.user_id === backendUser.user_id)

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
    ficha_mock: fallbackUser?.ficha_mock,
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
 *
 * NOTE: `id` must equal `user_id` so handleUserChange (which uses u.id) works
 * when the backend is offline and users come from this array.
 *
 * `ficha_mock.segmentos` must mirror the structure the backend returns via SSE
 * so FichaSidebar renders segment cards correctly even without a live request.
 */
const FALLBACK_USERS: DemoUser[] = [
  {
    id: 'USR-00001',
    user_id: 'USR-00001',
    name: 'Carla Mendoza',
    avatar: '👩‍💻',
    description: 'Actividad atípica · Presión financiera',
    segment: 'actividad_atipica_alerta',
    segment_labels: ['actividad_atipica_alerta', 'presion_financiera'],
    theme_color: '#00C389',
    sample_questions: [
      { text: 'Verificar identidad' },
      { text: '¿Cuál es mi saldo actual?' },
      { text: '¿Cuáles son mis últimos movimientos?' },
      { text: '¿Cómo puedo hacer una transferencia?' },
    ],
    ficha_mock: {
      user_id: 'USR-00001',
      segment: 'actividad_atipica_alerta',
      segmentos: {
        conductual: { name: 'actividad_atipica_alerta', label: 'Actividad atípica' },
        transaccional: { name: 'comprador_presencial_frecuente', label: 'Comprador presencial', top_spending_categories: ['Retail', 'Supermercado', 'Gasolina'] },
        salud_financiera: { name: 'presion_financiera', label: 'Presión financiera', offer_strategy: 'Educación financiera, no venta agresiva' },
      },
      digitalizacion: 'media',
      gasto: 3500,
      ahorro: 2100,
      inversion: 0,
      credito: 8900,
      top_categories: ['Retail', 'Supermercado', 'Gasolina'],
      health_score: 45,
      offer_strategy: 'Educación financiera, no venta agresiva',
      risk_level: 'high',
    },
  },
  {
    id: 'USR-00042',
    user_id: 'USR-00042',
    name: 'Javier López',
    avatar: '👨‍💼',
    description: 'Profesional · Inversor activo',
    segment: 'profesional_prospero_inversor',
    segment_labels: ['profesional_prospero_inversor', 'activo_saludable'],
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cuál es mi rendimiento en inversiones este mes?' },
      { text: '¿Qué productos de inversión me recomiendas?' },
      { text: '¿Cuál es el GAT real de mi cuenta?' },
      { text: '¿Puedo abrir un fondo indexado?' },
    ],
    ficha_mock: {
      user_id: 'USR-00042',
      segment: 'profesional_prospero_inversor',
      segmentos: {
        conductual: { name: 'profesional_prospero_inversor', label: 'Profesional próspero' },
        transaccional: { name: 'ahorrador_inversor', label: 'Ahorrador inversor', top_spending_categories: ['Inversiones', 'Restaurantes', 'Viajes'] },
        salud_financiera: { name: 'activo_saludable', label: 'Activo saludable', offer_strategy: 'Productos premium, inversión y patrimonio' },
      },
      digitalizacion: 'alta',
      gasto: 12500,
      ahorro: 45000,
      inversion: 250000,
      credito: 15000,
      top_categories: ['Inversiones', 'Restaurantes', 'Viajes'],
      health_score: 95,
      offer_strategy: 'Productos premium, inversión y patrimonio',
      risk_level: 'low',
    },
  },
  {
    id: 'USR-00108',
    user_id: 'USR-00108',
    name: 'Ana Torres',
    avatar: '👩‍🎓',
    description: 'Joven digital · Hey Pro',
    segment: 'joven_digital_hey_pro',
    segment_labels: ['joven_digital_hey_pro', 'en_construccion_crediticia'],
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cuánto cashback acumulé este mes?' },
      { text: '¿Qué hay de nuevo en Hey Shop?' },
      { text: '¿Cómo activo CoDi?' },
      { text: '¿Puedo subir mi límite de crédito?' },
    ],
    ficha_mock: {
      user_id: 'USR-00108',
      segment: 'joven_digital_hey_pro',
      segmentos: {
        conductual: { name: 'joven_digital_hey_pro', label: 'Joven digital Hey Pro' },
        transaccional: { name: 'consumidor_digital_ocio', label: 'Consumidor digital', top_spending_categories: ['Streaming', 'Juegos', 'Comida a domicilio'] },
        salud_financiera: { name: 'en_construccion_crediticia', label: 'En construcción crediticia', offer_strategy: 'Construcción de historial y cashback' },
      },
      digitalizacion: 'muy_alta',
      gasto: 4200,
      ahorro: 8500,
      inversion: 5000,
      credito: 3000,
      top_categories: ['Streaming', 'Juegos', 'Comida a domicilio'],
      health_score: 78,
      offer_strategy: 'Construcción de historial y cashback',
      risk_level: 'medium',
    },
  },
  {
    id: 'USR-00205',
    user_id: 'USR-00205',
    name: 'Roberto Sánchez',
    avatar: '👨‍🔧',
    description: 'Cliente estable · Perfil promedio',
    segment: 'cliente_promedio_estable',
    segment_labels: ['cliente_promedio_estable', 'activo_saludable'],
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cuál es mi saldo?' },
      { text: '¿Puedo hacer una transferencia?' },
      { text: '¿Qué beneficios tengo con mi cuenta?' },
      { text: '¿Cómo activo Hey Pro?' },
    ],
    ficha_mock: {
      user_id: 'USR-00205',
      segment: 'cliente_promedio_estable',
      segmentos: {
        conductual: { name: 'cliente_promedio_estable', label: 'Cliente estable' },
        transaccional: { name: 'pagador_servicios_hogar', label: 'Pagador servicios', top_spending_categories: ['Servicios', 'Supermercado', 'Educación'] },
        salud_financiera: { name: 'activo_saludable', label: 'Activo saludable', offer_strategy: 'Upsell gradual: Hey Pro, seguros, inversión básica' },
      },
      digitalizacion: 'media',
      gasto: 5800,
      ahorro: 12000,
      inversion: 8000,
      credito: 5000,
      top_categories: ['Servicios', 'Supermercado', 'Educación'],
      health_score: 82,
      offer_strategy: 'Upsell gradual: Hey Pro, seguros, inversión básica',
      risk_level: 'low',
    },
  },
  {
    id: 'USR-00310',
    user_id: 'USR-00310',
    name: 'María González',
    avatar: '👩‍💼',
    description: 'Estrés financiero · Apoyo prioritario',
    segment: 'usuario_estres_financiero',
    segment_labels: ['usuario_estres_financiero', 'presion_financiera'],
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Puedo reestructurar mi deuda?' },
      { text: '¿Cuánto debo en total?' },
      { text: '¿Hay algún plan de pagos disponible?' },
      { text: '¿Puedo pausar un pago este mes?' },
    ],
    ficha_mock: {
      user_id: 'USR-00310',
      segment: 'usuario_estres_financiero',
      segmentos: {
        conductual: { name: 'usuario_estres_financiero', label: 'Estrés financiero' },
        transaccional: { name: 'pagador_servicios_hogar', label: 'Pagador servicios', top_spending_categories: ['Renta', 'Servicios', 'Farmacia'] },
        salud_financiera: { name: 'presion_financiera', label: 'Presión financiera', offer_strategy: 'Reestructuración de deuda, planes de pago, no venta' },
      },
      digitalizacion: 'baja',
      gasto: 6500,
      ahorro: 1200,
      inversion: 0,
      credito: 22000,
      top_categories: ['Renta', 'Servicios', 'Farmacia'],
      health_score: 38,
      offer_strategy: 'Reestructuración de deuda, planes de pago, no venta',
      risk_level: 'high',
    },
  },
  {
    id: 'USR-00415',
    user_id: 'USR-00415',
    name: 'Carlos Mendivil',
    avatar: '🧑‍💻',
    description: 'Usuario básico · Nuevo cliente',
    segment: 'usuario_basico_bajo_enganche',
    segment_labels: ['usuario_basico_bajo_enganche', 'solido_sin_credito'],
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cómo funciona la cuenta Hey?' },
      { text: '¿Cómo deposito dinero?' },
      { text: '¿Hay comisiones?' },
      { text: '¿Puedo solicitar una tarjeta de crédito?' },
    ],
    ficha_mock: {
      user_id: 'USR-00415',
      segment: 'usuario_basico_bajo_enganche',
      segmentos: {
        conductual: { name: 'usuario_basico_bajo_enganche', label: 'Usuario básico' },
        transaccional: { name: 'comprador_presencial_frecuente', label: 'Comprador presencial', top_spending_categories: ['Supermercado', 'Farmacia', 'Transporte'] },
        salud_financiera: { name: 'solido_sin_credito', label: 'Sólido sin crédito', offer_strategy: 'Primer crédito, ahorro automatizado, educación' },
      },
      digitalizacion: 'media',
      gasto: 2100,
      ahorro: 3500,
      inversion: 0,
      credito: 0,
      top_categories: ['Supermercado', 'Farmacia', 'Transporte'],
      health_score: 65,
      offer_strategy: 'Primer crédito, ahorro automatizado, educación',
      risk_level: 'low',
    },
  },
  {
    id: 'USR-00520',
    user_id: 'USR-00520',
    name: 'Daniela Ruiz',
    avatar: '👩‍🎨',
    description: 'Empresaria · Alto volumen operativo',
    segment: 'empresario_alto_volumen',
    segment_labels: ['empresario_alto_volumen', 'activo_saludable'],
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cómo configuro nómina para mi empresa?' },
      { text: '¿Puedo facturar directamente desde Hey?' },
      { text: '¿Hay crédito PYME disponible?' },
      { text: '¿Cómo manejo transferencias de alto volumen?' },
    ],
    ficha_mock: {
      user_id: 'USR-00520',
      segment: 'empresario_alto_volumen',
      segmentos: {
        conductual: { name: 'empresario_alto_volumen', label: 'Empresario activo' },
        transaccional: { name: 'viajero_internacional', label: 'Viajero internacional', top_spending_categories: ['Proveedores', 'Viajes de negocios', 'Software'] },
        salud_financiera: { name: 'activo_saludable', label: 'Activo saludable', offer_strategy: 'Cuenta empresarial, nómina, crédito PYME, facturación' },
      },
      digitalizacion: 'muy_alta',
      gasto: 45000,
      ahorro: 80000,
      inversion: 120000,
      credito: 35000,
      top_categories: ['Proveedores', 'Viajes de negocios', 'Software'],
      health_score: 92,
      offer_strategy: 'Cuenta empresarial, nómina, crédito PYME, facturación',
      risk_level: 'low',
    },
  },
  {
    id: 'USR-00630',
    user_id: 'USR-00630',
    name: 'Luis Fernández',
    avatar: '👨‍🌾',
    description: 'Ahorrador · Construyendo historial',
    segment: 'en_construccion_crediticia',
    segment_labels: ['en_construccion_crediticia', 'consumidor_digital_ocio'],
    theme_color: '#00C389',
    sample_questions: [
      { text: '¿Cómo mejoro mi score buró?' },
      { text: '¿Cuánto he ahorrado este mes?' },
      { text: '¿Me conviene una tarjeta garantizada?' },
      { text: '¿Cuál es mi historial de pagos reciente?' },
    ],
    ficha_mock: {
      user_id: 'USR-00630',
      segment: 'en_construccion_crediticia',
      segmentos: {
        conductual: { name: 'en_construccion_crediticia', label: 'En construcción' },
        transaccional: { name: 'consumidor_digital_ocio', label: 'Consumidor digital', top_spending_categories: ['Entretenimiento', 'Comida', 'Ropa'] },
        salud_financiera: { name: 'en_construccion_crediticia', label: 'Construyendo historial', offer_strategy: 'Tarjeta garantizada, reporte de pagos, educación' },
      },
      digitalizacion: 'media',
      gasto: 3800,
      ahorro: 15000,
      inversion: 2000,
      credito: 2000,
      top_categories: ['Entretenimiento', 'Comida', 'Ropa'],
      health_score: 71,
      offer_strategy: 'Tarjeta garantizada, reporte de pagos, educación',
      risk_level: 'medium',
    },
  },
]
