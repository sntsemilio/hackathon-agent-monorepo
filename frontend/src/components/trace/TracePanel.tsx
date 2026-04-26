import { NodeTrace } from '../../types';
import { TraceNode } from './TraceNode';
import { ScrollArea } from '../ui/scroll-area';

interface TracePanelProps {
  traces: NodeTrace[];
}

// The fixed LangGraph pipeline
const PIPELINE_NODES = [
  'FichaInjector',
  'Guardrail',
  'Profiler',
  'Router',
  'Research/ToolOps', // Combine subgraphs for display
  'Summarizer'
];

export function TracePanel({ traces }: TracePanelProps) {
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-100 bg-white/80 backdrop-blur-md sticky top-0 z-10">
        <h2 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-[var(--hey-primary)] animate-pulse" />
          Agent Trace
        </h2>
        <p className="text-xs text-gray-500 mt-1 font-medium">
          Auditoría de nodos en tiempo real
        </p>
      </div>
      
      <ScrollArea className="flex-1 p-6">
        <div className="relative pl-4 space-y-8 pb-10">
          {/* Vertical connection line */}
          <div className="absolute top-2 bottom-2 left-[23px] w-px bg-border/50" />
          
          {PIPELINE_NODES.map((nodeName, idx) => {
            // Find if this node is in traces
            // For Research/ToolOps, match either
            const activeTrace = traces.find(t => {
              if (nodeName === 'Research/ToolOps') {
                return t.node === 'research' || t.node === 'tool_ops' || t.node === 'Research' || t.node === 'ToolOps';
              }
              return t.node.toLowerCase() === nodeName.toLowerCase();
            });

            // If we have traces beyond this node, it's done (if it was skipped, it's gray)
            let status: 'pending' | 'running' | 'done' = 'pending';
            let latency: number | undefined;
            let explanation: string | undefined;

            if (activeTrace) {
              status = activeTrace.status;
              latency = activeTrace.latency_ms;
              explanation = activeTrace.explanation;
            } else {
              // Heuristic: if a later node is running/done, this one was bypassed or done instantly
              const currentIndexInTraces = traces.findIndex(t => 
                t.node.toLowerCase() === nodeName.toLowerCase()
              );
              // Not robust but good enough for UI illusion if traces skip
            }

            return (
              <TraceNode 
                key={nodeName}
                name={nodeName}
                status={status}
                latency={latency}
                explanation={explanation}
                isLast={idx === PIPELINE_NODES.length - 1}
              />
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
