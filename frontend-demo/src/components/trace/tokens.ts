import {
  User,
  Shield,
  Brain,
  Map,
  Database,
  Settings,
  FileText,
  Sparkles,
  LucideIcon,
} from 'lucide-react'

export type TraceStatus = 'pending' | 'running' | 'done' | 'error'

export const NODE_LABELS: Record<string, string> = {
  ficha_injector: 'Inyectar ficha del cliente',
  guardrail_check: 'Validar guardrails',
  guardrail: 'Validar guardrails',
  profiler: 'Perfilar segmento',
  plan_research: 'Plan de búsqueda',
  gather_context: 'Recuperar contexto (RAG)',
  tool_ops: 'Operaciones bancarias',
  draft_response: 'Generar respuesta',
  draft_response_gen: 'Generar respuesta',
  summarizer: 'Personalización final',
}

export const NODE_TONES: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'neutral'> = {
  ficha_injector: 'success',
  guardrail_check: 'success',
  guardrail: 'success',
  profiler: 'purple',
  plan_research: 'info',
  gather_context: 'info',
  tool_ops: 'neutral',
  draft_response: 'success',
  draft_response_gen: 'success',
  summarizer: 'success',
}

export const NODE_ICONS: Record<string, LucideIcon> = {
  ficha_injector: User,
  guardrail_check: Shield,
  guardrail: Shield,
  profiler: Brain,
  plan_research: Map,
  gather_context: Database,
  tool_ops: Settings,
  draft_response: FileText,
  draft_response_gen: FileText,
  summarizer: Sparkles,
}

export const TONE_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  success: { bg: 'rgba(0,195,137,0.12)', color: '#3FDDA8', border: 'rgba(0,195,137,0.30)' },
  warning: { bg: 'rgba(255,140,66,0.12)', color: '#FFA869', border: 'rgba(255,140,66,0.30)' },
  danger: { bg: 'rgba(239,68,68,0.12)', color: '#F87171', border: 'rgba(239,68,68,0.30)' },
  info: { bg: 'rgba(59,130,246,0.12)', color: '#60A5FA', border: 'rgba(59,130,246,0.30)' },
  purple: { bg: 'rgba(107,78,255,0.15)', color: '#A89BFF', border: 'rgba(107,78,255,0.35)' },
  neutral: { bg: 'rgba(139,148,158,0.10)', color: '#8B949E', border: 'rgba(139,148,158,0.25)' },
}

export const STATUS_BADGE: Record<TraceStatus, { label: string; bg: string; color: string }> = {
  done: { label: 'done', bg: 'rgba(0,195,137,0.15)', color: '#3FDDA8' },
  running: { label: 'running', bg: 'rgba(255,140,66,0.15)', color: '#FFA869' },
  error: { label: 'error', bg: 'rgba(239,68,68,0.15)', color: '#F87171' },
  pending: { label: 'pending', bg: 'rgba(139,148,158,0.12)', color: '#8B949E' },
}
