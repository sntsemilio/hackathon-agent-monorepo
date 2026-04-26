export interface SampleQuestion {
  text: string
  category?: string
}

export interface DemoUser {
  id?: string
  name: string
  user_id: string
  avatar: string
  segment_labels?: string[]
  segment?: string
  theme_color?: string
  questions?: SampleQuestion[] | string[]
  sample_questions?: SampleQuestion[] | string[]
  description?: string
  ficha_mock?: Ficha
}

export interface User {
  id: string
  name: string
  user_id?: string
  avatar?: string
  segment_labels?: string[]
  questions?: any[]
}

export interface TraceSpan {
  node: string
  status: 'done' | 'running' | 'error'
  latency_ms?: number
  metadata?: Record<string, any>
  explanation?: string
  data?: any
}

export interface ActionCard {
  id: string
  title: string
  cta: string
  deep_link?: string
  icon?: string
}

export type ActionCardData = ActionCard

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  isStreaming?: boolean
  action_cards?: ActionCard[]
  tool_call?: any
  node_traces?: TraceSpan[]
  latency_ms?: number
  tokens?: number
  /** 'insight' = mensaje proactivo de Havi (estilo visual diferente) */
  variant?: 'insight'
}

export type Message = ChatMessage

export interface ToolCallIntent {
  tool_call_id: string
  tool_name: string
  params: Record<string, any>
  description?: string
}

export interface FichaSegmento {
  name?: string
  tone?: string
  label?: string
  offer_strategy?: string
  top_spending_categories?: string[]
  confidence?: number
}

export interface Ficha {
  user_id?: string
  segmentos?: {
    conductual?: FichaSegmento
    transaccional?: FichaSegmento
    salud_financiera?: FichaSegmento
  }
  sugerencias_candidatas?: string[]
  version?: string
  segment?: string
  digitalizacion?: string
  gasto?: number
  ahorro?: number
  inversion?: number
  credito?: number
  top_categories?: string[]
  health_score?: number
  offer_strategy?: string
  risk_level?: 'low' | 'medium' | 'high'
}

export type ClientFicha = Ficha

export interface ConversationalProfile {
  intent?: string
  sentiment?: 'positive' | 'neutral' | 'negative'
  urgency?: 'low' | 'medium' | 'high'
  formality?: 'formal' | 'casual'
  topic?: string
  behavioral_segment?: string
  transactional_segment?: string
  financial_health_segment?: string
  offer_strategy?: string
  risk_level?: 'low' | 'medium' | 'high'
}

export interface ProactiveInsight {
  type: string
  title: string
  body: string
  action_card?: ActionCard
  timestamp?: string
  user_id?: string
}

export interface BackendDemoUser {
  user_id: string
  name: string
  avatar: string
  description: string
  segment_labels: string[]
  sample_questions: string[]
}

export interface BackendMetrics {
  requests_total: number
  token_usage_total: number
  tokens_per_request: number
  avg_latency_ms: number
  success_rate: number
  delegation_trace_count: number
  latest_trace: Array<{
    timestamp: string
    user_id: string
    query: string
    status_label: string
    latency_ms: number
    estimated_cost: number
  }>
  rag_metrics?: {
    retrieval_success_rate: number
    avg_retrieval_latency_ms: number
    avg_rerank_latency_ms: number
  }
}

export interface EvaluationMetrics {
  faithfulness: number
  answer_relevancy: number
  context_precision: number
  context_recall: number
  f1_score: number
  last_run: string
  test_cases_passed: number
  test_cases_failed: number
}
