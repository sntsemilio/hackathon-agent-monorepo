import { ChatMessage } from '../../types';
import { motion } from 'framer-motion';
import { ActionCard } from './ActionCard';
import { Info } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '../ui/tooltip';
import ReactMarkdown from 'react-markdown';

interface ChatBubbleProps {
  message: ChatMessage;
  onExplain?: () => void;
}

export function ChatBubble({ message, onExplain }: ChatBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`flex flex-col max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        
        {/* Main Bubble */}
        <div className={`
          relative px-4 py-3 rounded-3xl text-[15px] leading-relaxed
          ${isUser 
            ? 'bg-[var(--hey-primary)] text-white rounded-br-sm shadow-md' 
            : 'bg-white border-0 text-foreground rounded-bl-sm shadow-sm'
          }
        `}>
          {message.isStreaming ? (
             <div className="flex items-center gap-1">
               <span className="opacity-70">{message.content}</span>
               <span className="w-1.5 h-4 bg-gray-400 animate-pulse rounded-sm" />
             </div>
          ) : (
            <div className={`prose prose-p:leading-relaxed prose-pre:bg-gray-50 prose-pre:border-0 max-w-none ${isUser ? 'prose-invert text-white' : 'text-gray-800'}`}>
              <ReactMarkdown>{message.content || '...'}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Action Cards */}
        {!isUser && message.action_cards && message.action_cards.length > 0 && (
          <div className="mt-3 flex flex-col gap-2 w-full max-w-sm">
            {message.action_cards.map(card => (
              <ActionCard key={card.id} card={card} />
            ))}
          </div>
        )}

        {/* Explain Button (Agent only, and not streaming) */}
        {!isUser && !message.isStreaming && message.node_traces && message.node_traces.length > 0 && (
          <div className="mt-2 pl-1">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button 
                    onClick={onExplain}
                    className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors group"
                  >
                    <Info className="w-3.5 h-3.5 group-hover:text-[var(--hey-primary)] transition-colors" />
                    <span>Explicar esto</span>
                  </button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Ver el árbol de ejecución (trace) de esta respuesta</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )}
      </div>
    </motion.div>
  );
}
