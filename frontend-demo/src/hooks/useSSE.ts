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
  // Used to cancel in-flight greetings when the user switches again rapidly
  const greetGenRef = useRef(0)

  const clearMessages = useCallback(() => {
    setMessages([])
    setCurrentTrace([])
    setFicha(null)
    setProfile(null)
  }, [])

  /**
   * Clears the chat and animates a personalized greeting from Havi with a
   * typewriter effect. If `insight` is provided, it appears as a second
   * proactive message ~1 s after the greeting finishes.
   * Safe to call rapidly — only the last call "wins".
   */
  const greetUser = useCallback(async (greeting: string, insight?: string) => {
    // Cancel any in-progress API call
    if (abortRef.current) abortRef.current.abort()

    // Reset all state
    setMessages([])
    setCurrentTrace([])
    setFicha(null)
    setProfile(null)

    if (!greeting) return

    // Bump generation counter so a previous greeting loop will bail out
    const gen = ++greetGenRef.current

    // Let React flush the clearMessages state before we start writing
    await new Promise(r => setTimeout(r, 60))
    if (greetGenRef.current !== gen) return

    // ── Greeting typewriter ─────────────────────────────────────────────
    const greetMsg: Message = {
      id: `greeting-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    }
    setMessages([greetMsg])

    for (let i = 1; i <= greeting.length; i++) {
      if (greetGenRef.current !== gen) return
      await new Promise(r => setTimeout(r, 14))
      setMessages([{ ...greetMsg, content: greeting.slice(0, i) }])
    }

    // ── Proactive insight typewriter (aparece ~1 s después) ─────────────
    if (!insight) return

    // Pausa antes del insight — simula que Havi "analizó" la cuenta
    await new Promise(r => setTimeout(r, 950))
    if (greetGenRef.current !== gen) return

    const insightMsg: Message = {
      id: `insight-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      variant: 'insight',
    }
    setMessages(prev => [...prev, insightMsg])

    for (let i = 1; i <= insight.length; i++) {
      if (greetGenRef.current !== gen) return
      await new Promise(r => setTimeout(r, 16))
      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last?.id === insightMsg.id) {
          updated[updated.length - 1] = { ...last, content: insight.slice(0, i) }
        }
        return updated
      })
    }
  }, [])

  const sendMessage = useCallback(async (message: string, userId: string | null) => {
    setIsStreaming(true)
    setCurrentTrace([])

    const userMsg: Message = {
      id: `msg-${Date.now()}-${Math.random()}`,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, userMsg])

    const body: Record<string, any> = {
      message,
      user_id: userId || 'anonymous',
      session_id: `session-${Date.now()}`,
      personalization_enabled: !!userId,
    }

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

                // Extract profile from profiler trace (backend sends 'profiler', not 'profiler_slm')
                if ((data.node === 'profiler' || data.node === 'profiler_slm') && data.metadata?.profile) {
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
          id: `msg-${Date.now()}-${Math.random()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          action_cards: actionCards.length > 0 ? actionCards : undefined,
          node_traces: traceSpans,
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
          id: `msg-${Date.now()}-${Math.random()}`,
          role: 'assistant',
          content: `Lo siento, hubo un error al conectar con el servidor. Verifica que el backend esté corriendo en ${API_BASE}.`,
          timestamp: new Date().toISOString(),
        }
        setMessages(prev => [...prev, errMsg])
      }
    } finally {
      setIsStreaming(false)
    }
  }, [])

  return { messages, currentTrace, ficha, profile, isStreaming, sendMessage, clearMessages, greetUser }
}
