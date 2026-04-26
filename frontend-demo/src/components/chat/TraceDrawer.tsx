import { ChatMessage } from '../../types';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '../ui/sheet';
import { ScrollArea } from '../ui/scroll-area';
import { Activity, Clock } from 'lucide-react';
import { Badge } from '../ui/badge';

interface TraceDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  message?: ChatMessage;
}

export function TraceDrawer({ open, onOpenChange, message }: TraceDrawerProps) {
  if (!message || !message.node_traces) return null;

  const totalLatency = message.node_traces.reduce((acc, t) => acc + (t.latency_ms || 0), 0);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[400px] sm:w-[540px] bg-card border-l border-border p-0 flex flex-col">
        
        <SheetHeader className="p-6 border-b border-border bg-background/50">
          <SheetTitle className="flex items-center gap-2 text-[var(--hey-primary)]">
            <Activity className="w-5 h-5" />
            Trace Execution
          </SheetTitle>
          <SheetDescription>
            Detalle de la ejecución del grafo para este mensaje.
          </SheetDescription>
          
          <div className="flex items-center gap-4 mt-4 text-sm">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Clock className="w-4 h-4" />
              <span>Total: <span className="font-medium text-foreground">{totalLatency}ms</span></span>
            </div>
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <span>Nodos: <span className="font-medium text-foreground">{message.node_traces.length}</span></span>
            </div>
          </div>
        </SheetHeader>

        <ScrollArea className="flex-1 p-6">
          <div className="space-y-6">
            {message.node_traces.map((trace, idx) => (
              <div key={idx} className="relative pl-6">
                
                {/* Line */}
                {idx !== message.node_traces!.length - 1 && (
                  <div className="absolute left-[11px] top-6 bottom-[-24px] w-px bg-border" />
                )}
                
                {/* Dot */}
                <div className="absolute left-[8px] top-1.5 w-2 h-2 rounded-full bg-[var(--hey-primary)]" />
                
                {/* Content */}
                <div className="bg-muted/30 rounded-lg p-3 border border-border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm text-foreground">{trace.node}</span>
                    <Badge variant="outline" className="text-[10px] font-mono text-muted-foreground">
                      {trace.latency_ms}ms
                    </Badge>
                  </div>
                  
                  {trace.explanation && (
                    <p className="text-xs text-muted-foreground">
                      {trace.explanation}
                    </p>
                  )}
                  
                  {/* Detailed data view (optional, if we want to show raw JSON) */}
                  {trace.data && Object.keys(trace.data).length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border">
                      <pre className="text-[10px] text-muted-foreground overflow-x-auto">
                        {JSON.stringify(trace.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
