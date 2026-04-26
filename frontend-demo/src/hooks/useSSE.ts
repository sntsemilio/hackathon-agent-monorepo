import { useState, useCallback, useRef } from 'react'
import { Message, TraceSpan, Ficha, ActionCard } from '../types'

const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface ConversationalProfile {
  intent?: string
  sentiment?: 'positive' | 'neutral' | 'negative'
  urgency?: 'low' | 'medium' | 'high'
  formality?: 'casual' | 'neutral' | 'formal'
  topic?: string | null
  mentions_money_amount?: boolean
  behavioral_segment?: string | null
  transactional_segment?: string | null
  financial_health_segment?: string | null
  top_spending_categories?: string[]
  offer_strategy?: string | null
  candidate_suggestions?: string[]
  persona_key?: string | null
}

export function useSSE() {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentTrace, setCurrentTrace] = useState<TraceSpan[]>([])
  const [ficha, setFicha] = useState<Ficha | null>(null)
  const [profile, setProfile] = useState<ConversationalProfile | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const clearMessages = useCallback(() => {
    setMessages([])
    setCurrentTrace([])
    setFicha(null)
    setProfile(null)
  }, [])

  const sendMessage = useCallback(async (message: string, userId: string | null) => {
    setIsStreaming(true)
    setCurrentTrace([])

    const userMsg: Message = {
      role: 'user',
      content: message,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])

    const body: Record<string, any> = { message }
    if (userId) body.user_id = userId

    abortRef.current = new AbortController()

    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: abortRef.current.signal,
      })

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finalResponse = ''
      let actionCards: ActionCard[] = []
      let traceSpans: TraceSpan[] = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            const dataStr = line.slice(5).trim()
            if (!dataStr) continue
            try {
              const data = JSON.parse(dataStr)

              if (currentEvent === 'trace') {
                const span: TraceSpan = {
                  node: data.node || data.span || 'unknown',
                  latency_ms: data.latency_ms || 0,
                  status: data.status || 'done',
                  metadata: data.metadata || data,
                }

                // Extract ficha from ficha_injector trace
                if (data.node === 'ficha_injector' && data.metadata?.ficha_cliente) {
                  setFicha(data.metadata.ficha_cliente)
                }

                // Extract profile from profiler_slm trace
                if (data.node === 'profiler_slm' && data.metadata?.profile) {
                  setProfile(data.metadata.profile)
                }

                // Also check top-level ficha in final event
                if (data.ficha && !data.node) {
                  setFicha(data.ficha)
                }

                traceSpans = [...traceSpans, span]
                setCurrentTrace([...traceSpans])
              } else if (currentEvent === 'final') {
                finalResponse = data.response || data.text || ''
                if (data.action_cards) {
                  actionCards = data.action_cards
                }
                if (data.ficha) {
                  setFicha(data.ficha)
                }
              } else if (currentEvent === 'error') {
                finalResponse = `Error: ${data.detail || data.message || 'Error desconocido'}`
              }
            } catch {
              // non-JSON data line, ignore
            }
            currentEvent = ''
          }
        }
      }

      // Typewriter effect
      if (finalResponse) {
        const assistantMsg: Message = {
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          action_cards: actionCards.length > 0 ? actionCards : undefined,
          trace: traceSpans,
        }
        setMessages(prev => [...prev, assistantMsg])

        for (let i = 0; i <= finalResponse.length; i++) {
          await new Promise(r => setTimeout(r, 12))
          const partial = finalResponse.slice(0, i)
          setMessages(prev => {
            const updated = [...prev]
            const last = updated[updated.length - 1]
            if (last.role === 'assistant') {
              updated[updated.length - 1] = { ...last, content: partial }
            }
            return updated
          })
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        const errMsg: Message = {
          role: 'assistant',
          content: `Lo siento, hubo un error al conectar con el servidor. Verifica que el backend esté corriendo en ${API_BASE}.`,
          timestamp: Date.now(),
        }
        setMessages(prev => [...prev, errMsg])
      }
    } finally {
      setIsStreaming(false)
    }
  }, [])

  return { messages, currentTrace, ficha, profile, isStreaming, sendMessage, clearMessages }
}
