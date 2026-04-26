export interface User {
  id: string;
  name: string;
  segment: string;
  color: string;
  questions: string[];
}

export interface NodeTrace {
  node: string;
  status: 'pending' | 'running' | 'done';
  latency_ms?: number;
  explanation?: string;
  data?: any;
}

export interface ActionCardData {
  id: string;
  title: string;
  icon?: string;
  cta: string;
  deep_link: string;
}

export interface ToolCallIntent {
  tool_call_id: string;
  tool_name: string;
  params: Record<string, any>;
  description?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: number;
  action_cards?: ActionCardData[];
  tool_call?: ToolCallIntent;
  isStreaming?: boolean;
  node_traces?: NodeTrace[];
}

export interface ClientFicha {
  segment: string;
  digitalizacion: number;
  gasto: number;
  ahorro: number;
  inversion: number;
  credito: number;
  top_categories: { name: string; amount: number; color: string }[];
  health_score: number;
}

export interface ProactiveInsight {
  type: string;
  title: string;
  body: string;
  action_card?: ActionCardData;
  timestamp: number;
  user_id: string;
}
