import { useState, useCallback, useRef } from 'react';
import { ChatMessage, NodeTrace, ToolCallIntent, ClientFicha } from '../types';

interface UseSSEChatOptions {
  userId: string;
  sessionId?: string;
  personalizationEnabled: boolean;
}

export function useSSEChat({ userId, sessionId, personalizationEnabled }: UseSSEChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [traces, setTraces] = useState<NodeTrace[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [pendingToolCall, setPendingToolCall] = useState<ToolCallIntent | null>(null);
  const [ficha, setFicha] = useState<ClientFicha | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: Date.now(),
    };
    
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    setTraces([]);

    try {
      const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          message: content,
          session_id: sessionId,
          personalization_enabled: personalizationEnabled,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok || !response.body) throw new Error('Stream failed');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      let currentAgentMsgId = Date.now().toString() + '-agent';
      setMessages(prev => [
        ...prev,
        {
          id: currentAgentMsgId,
          role: 'agent',
          content: '',
          timestamp: Date.now(),
          isStreaming: true,
          node_traces: [],
        }
      ]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (!dataStr.trim()) continue;

            try {
              const event = JSON.parse(dataStr);
              handleEvent(event, currentAgentMsgId);
            } catch (e) {
              console.error('Error parsing SSE event:', e);
            }
          }
        }
      }
      
      // Mark as not streaming
      setMessages(prev => prev.map(msg => 
        msg.id === currentAgentMsgId ? { ...msg, isStreaming: false } : msg
      ));
      
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        console.error('SSE Error:', err);
      }
    } finally {
      setIsStreaming(false);
    }
  }, [userId, sessionId, personalizationEnabled]);

  const handleEvent = (event: any, msgId: string) => {
    switch (event.event) {
      case 'node_update':
        setTraces(prev => {
          const existing = prev.find(t => t.node === event.node);
          if (existing) {
            return prev.map(t => t.node === event.node ? { ...t, data: event.data, status: 'running' } : t);
          }
          return [...prev, { node: event.node, status: 'running', data: event.data }];
        });
        
        // Handle client ficha if it comes in node_update (e.g. Profiler / FichaInjector)
        if (event.data?.ficha_cliente) {
           setFicha(event.data.ficha_cliente);
        }
        
        // Stream text if it's in final_response or current node
        if (event.data?.final_response) {
          setMessages(prev => prev.map(msg => 
            msg.id === msgId ? { ...msg, content: event.data.final_response } : msg
          ));
        } else if (event.data?.draft_response) {
          setMessages(prev => prev.map(msg => 
            msg.id === msgId ? { ...msg, content: event.data.draft_response } : msg
          ));
        }
        break;

      case 'trace_update':
        setTraces(prev => {
          // Attempt to map trace to node based on trace data
          // Simplified: append or update trace info
          const nodeName = event.data.node_name || 'System';
          const existing = prev.find(t => t.node === nodeName);
          if (existing) {
            return prev.map(t => t.node === nodeName ? { ...t, latency_ms: event.data.duration_ms, explanation: event.data.explanation || t.explanation } : t);
          }
          return [...prev, { node: nodeName, status: 'running', latency_ms: event.data.duration_ms, explanation: event.data.explanation }];
        });
        break;

      case 'tool_call_intent':
        setPendingToolCall(event.data);
        break;

      case 'trace_summary':
        // Mark all as done or update final latencies
        setTraces(prev => prev.map(t => ({ ...t, status: 'done' })));
        setMessages(prev => prev.map(msg => 
          msg.id === msgId ? { ...msg, node_traces: event.data.traces } : msg
        ));
        break;

      case 'done':
        setTraces(prev => prev.map(t => ({ ...t, status: 'done' })));
        break;
        
      case 'error':
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'agent',
          content: `Error: ${event.message}`,
          timestamp: Date.now()
        }]);
        break;
    }
  };

  const confirmToolCall = async (confirmed: boolean, toolName: string, params: any) => {
    if (!pendingToolCall) return;
    
    try {
      const res = await fetch('/chat/tool-execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_call_id: pendingToolCall.tool_call_id,
          user_id: userId,
          confirmed,
          tool_name: toolName,
          params
        })
      });
      
      const data = await res.json();
      setPendingToolCall(null);
      
      // Optionally trigger another chat message with the result
      if (confirmed && data.status === 'executed') {
         // Could auto-send "Continúa con el resultado" or backend might stream again
         sendMessage(`*Tool ejecutada: ${toolName}*`);
      }
    } catch (e) {
      console.error('Failed to confirm tool:', e);
    }
  };

  return {
    messages,
    traces,
    isStreaming,
    sendMessage,
    pendingToolCall,
    confirmToolCall,
    ficha,
  };
}
