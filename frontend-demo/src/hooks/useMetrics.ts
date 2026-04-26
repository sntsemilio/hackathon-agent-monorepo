// Hook para polling de métricas del backend
import { useState, useEffect, useCallback } from "react"

const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000"

export interface BackendMetrics {
  requests_total: number
  token_usage_total: number
  tokens_per_request: number
  avg_latency_ms: number
  success_rate: number
  delegation_trace_count: number
  latest_trace: TraceRow[]
  rag_metrics: {
    retrieval_success_rate: number
    avg_retrieval_latency_ms: number
    avg_rerank_latency_ms: number
  }
}

export interface TraceRow {
  timestamp: string
  user_id: string
  query: string
  status_label: string
  latency_ms: number
  estimated_cost: number
}

export interface EvalMetrics {
  faithfulness: number
  answer_relevancy: number
  context_precision: number
  context_recall: number
  f1_score: number
  last_run: string
  test_cases_passed: number
  test_cases_failed: number
}

export function useMetrics(pollIntervalMs = 2000) {
  const [metrics, setMetrics] = useState<BackendMetrics | null>(null)
  const [evals, setEvals] = useState<EvalMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/metrics`, {
        headers: { "Content-Type": "application/json" }
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setMetrics(data)
      setLastUpdated(new Date())
      setError(null)
    } catch (e) {
      // Si el endpoint no existe aún, usar datos de demo
      setMetrics(getDemoMetrics())
      setError(null) // no mostrar error en demo
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchEvals = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/evals/ragas`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setEvals(data)
    } catch {
      setEvals(getDemoEvals())
    }
  }, [])

  useEffect(() => {
    fetchMetrics()
    fetchEvals()
    const interval = setInterval(fetchMetrics, pollIntervalMs)
    return () => clearInterval(interval)
  }, [fetchMetrics, fetchEvals, pollIntervalMs])

  return { metrics, evals, loading, error, lastUpdated, refresh: fetchMetrics }
}

// ── Datos de demo cuando el backend no tiene el endpoint ──────

function getDemoMetrics(): BackendMetrics {
  const base = Math.floor(Date.now() / 1000) % 100
  return {
    requests_total: 12450 + base,
    token_usage_total: 1890000 + base * 357,
    tokens_per_request: 357,
    avg_latency_ms: 1200 + (base % 400),
    success_rate: 0.963,
    delegation_trace_count: 12 + base,
    latest_trace: [
      { timestamp: new Date(Date.now() - 95000).toTimeString().slice(0,8), user_id: "USR-00415", query: "Transferencia $100K · cuenta nueva", status_label: "pasó guards", latency_ms: 967, estimated_cost: 0.006 },
      { timestamp: new Date(Date.now() - 213000).toTimeString().slice(0,8), user_id: "USR-00108", query: "Reestructura de deuda", status_label: "plan creado", latency_ms: 617, estimated_cost: 0.005 },
      { timestamp: new Date(Date.now() - 357000).toTimeString().slice(0,8), user_id: "USR-00001", query: "Inversiones — empezar con poco", status_label: "Hey Pro sugerido", latency_ms: 549, estimated_cost: 0.004 },
      { timestamp: new Date(Date.now() - 549000).toTimeString().slice(0,8), user_id: "USR-08821", query: "Consulta de balance", status_label: "ok", latency_ms: 423, estimated_cost: 0.003 },
    ],
    rag_metrics: {
      retrieval_success_rate: 0.92,
      avg_retrieval_latency_ms: 280,
      avg_rerank_latency_ms: 45
    }
  }
}

function getDemoEvals(): EvalMetrics {
  return {
    faithfulness: 0.87,
    answer_relevancy: 0.92,
    context_precision: 0.78,
    context_recall: 0.85,
    f1_score: 0.89,
    last_run: new Date(Date.now() - 3600000).toISOString(),
    test_cases_passed: 45,
    test_cases_failed: 5
  }
}
