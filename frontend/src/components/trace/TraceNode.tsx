import { motion } from 'framer-motion';
import { Badge } from '../ui/badge';
import { Activity } from 'lucide-react';

interface TraceNodeProps {
  name: string;
  status: 'pending' | 'running' | 'done';
  latency?: number;
  explanation?: string;
  isLast?: boolean;
}

export function TraceNode({ name, status, latency, explanation, isLast }: TraceNodeProps) {
  
  const getDotStyle = () => {
    switch(status) {
      case 'running': return 'bg-yellow-400';
      case 'done': return 'bg-[var(--hey-primary)]';
      default: return 'bg-muted';
    }
  };

  const getBorderColor = () => {
    switch(status) {
      case 'running': return 'border-yellow-400/30';
      case 'done': return 'border-[var(--hey-primary)]/30';
      default: return 'border-border';
    }
  };

  return (
    <div className="relative group">
      {/* Node Dot */}
      <div className="absolute -left-[30px] top-1">
        <div className="relative flex h-4 w-4 items-center justify-center">
          {status === 'running' && (
            <motion.div 
              className="absolute h-full w-full rounded-full bg-yellow-400/40"
              animate={{ scale: [1, 1.8, 1], opacity: [0.8, 0, 0.8] }}
              transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
            />
          )}
          <div className={`h-2.5 w-2.5 rounded-full z-10 transition-colors duration-500 ${getDotStyle()}`} />
        </div>
      </div>

      {/* Content Card */}
      <div className={`
        relative p-3 rounded-xl border bg-card/40 transition-all duration-300
        ${status === 'running' ? 'shadow-[0_0_15px_rgba(250,204,21,0.1)]' : ''}
        ${getBorderColor()}
      `}>
        <div className="flex items-center justify-between mb-1">
          <span className={`font-medium text-sm transition-colors ${status === 'pending' ? 'text-muted-foreground' : 'text-foreground'}`}>
            {name}
          </span>
          {latency !== undefined && (
            <Badge variant="outline" className={`text-[10px] h-5 px-1.5 font-mono ${status === 'running' ? 'text-yellow-400 border-yellow-400/30' : 'text-muted-foreground'}`}>
              {latency}ms
            </Badge>
          )}
          {status === 'running' && latency === undefined && (
            <Activity className="w-3 h-3 text-yellow-400 animate-pulse" />
          )}
        </div>
        
        <motion.div 
          initial={{ height: 0, opacity: 0 }}
          animate={{ 
            height: explanation ? 'auto' : 0, 
            opacity: explanation ? 1 : 0 
          }}
          className="overflow-hidden"
        >
          <p className="text-xs text-muted-foreground leading-relaxed mt-1">
            {explanation}
          </p>
        </motion.div>
      </div>
    </div>
  );
}
