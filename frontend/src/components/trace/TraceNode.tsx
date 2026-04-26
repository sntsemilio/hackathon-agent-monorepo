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
      default: return 'bg-gray-300';
    }
  };

  const getBorderColor = () => {
    switch(status) {
      case 'running': return 'border-transparent ring-2 ring-yellow-400/30';
      case 'done': return 'border-transparent ring-2 ring-[var(--hey-primary)]/30';
      default: return 'border-transparent';
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
        relative p-4 rounded-xl bg-white shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md
        ${status === 'running' ? 'shadow-[0_4px_20px_rgba(250,204,21,0.15)]' : ''}
        ${getBorderColor()}
      `}>
        <div className="flex items-center justify-between mb-1">
          <span className={`font-bold text-sm transition-colors ${status === 'pending' ? 'text-gray-400' : (status === 'done' ? 'text-[var(--hey-primary)]' : 'text-foreground')}`}>
            {name}
          </span>
          {latency !== undefined && (
            <Badge variant="outline" className={`text-[10px] h-5 px-1.5 font-mono ${status === 'running' ? 'text-yellow-500 border-yellow-200 bg-yellow-50' : 'text-gray-500 bg-gray-50 border-gray-100'}`}>
              {latency}ms
            </Badge>
          )}
          {status === 'running' && latency === undefined && (
            <Activity className="w-3 h-3 text-yellow-500 animate-pulse" />
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
          <p className="text-xs text-gray-500 leading-relaxed mt-2">
            {explanation}
          </p>
        </motion.div>
      </div>
    </div>
  );
}
