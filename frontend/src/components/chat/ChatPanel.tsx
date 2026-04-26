import { useEffect, useRef, useState } from 'react';
import { User, ChatMessage, ToolCallIntent } from '../../types';
import { ChatBubble } from './ChatBubble';
import { QuestionChips } from './QuestionChips';
import { ConfirmationCard } from './ConfirmationCard';
import { Send, Mic, MicOff } from 'lucide-react';
import { ScrollArea } from '../ui/scroll-area';
import { TraceDrawer } from './TraceDrawer';

interface ChatPanelProps {
  user: User;
  messages: ChatMessage[];
  isStreaming: boolean;
  onSendMessage: (msg: string) => void;
  pendingToolCall: ToolCallIntent | null;
  onConfirmToolCall: (confirmed: boolean, toolName: string, params: any) => void;
  speech: any;
}

export function ChatPanel({
  user,
  messages,
  isStreaming,
  onSendMessage,
  pendingToolCall,
  onConfirmToolCall,
  speech
}: ChatPanelProps) {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming, pendingToolCall]);

  // Update input when speech transcript changes
  useEffect(() => {
    if (speech.transcript) {
      setInput(speech.transcript);
    }
  }, [speech.transcript]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleExplain = (msgId: string) => {
    setSelectedMessageId(msgId);
    setDrawerOpen(true);
  };

  const selectedMessage = messages.find(m => m.id === selectedMessageId);

  return (
    <>
      <div className="flex-1 flex flex-col relative bg-background/30 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-blend-overlay">
        
        {/* Messages Area */}
        <ScrollArea className="flex-1 px-6 pt-6">
          <div className="max-w-3xl mx-auto flex flex-col gap-6 pb-8" ref={scrollRef}>
            
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-40 text-muted-foreground mt-20">
                <p className="text-sm">Envía un mensaje a Havi para comenzar.</p>
              </div>
            )}

            {messages.map((msg) => (
              <ChatBubble 
                key={msg.id} 
                message={msg} 
                onExplain={() => handleExplain(msg.id)}
              />
            ))}

            {pendingToolCall && (
              <div className="flex justify-start max-w-[85%]">
                <ConfirmationCard 
                  toolCall={pendingToolCall}
                  onConfirm={(confirmed) => onConfirmToolCall(confirmed, pendingToolCall.tool_name, pendingToolCall.params)}
                />
              </div>
            )}
            
            {/* Dummy div to scroll to */}
            <div className="h-4" />
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="p-4 bg-background/80 backdrop-blur-md border-t border-border">
          <div className="max-w-3xl mx-auto flex flex-col gap-3">
            
            <QuestionChips 
              questions={user.questions} 
              onSelect={(q) => onSendMessage(q)} 
              disabled={isStreaming || !!pendingToolCall}
            />

            <form onSubmit={handleSubmit} className="relative flex items-end gap-2 bg-card border border-border rounded-2xl p-1 shadow-sm focus-within:ring-1 focus-within:ring-[var(--hey-primary)] transition-all">
              
              <button
                type="button"
                onClick={speech.isListening ? speech.stopListening : speech.startListening}
                className={`p-3 shrink-0 rounded-xl transition-colors ${speech.isListening ? 'bg-red-500/20 text-red-500' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}
                disabled={isStreaming || !!pendingToolCall || !speech.supported}
                title={speech.supported ? "Usar micrófono" : "Micrófono no soportado"}
              >
                {speech.isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
              </button>

              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                  }
                }}
                placeholder="Pregúntale a Havi..."
                className="flex-1 bg-transparent border-0 resize-none max-h-32 min-h-[44px] py-3 px-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-0 text-sm scrollbar-hide"
                rows={1}
                disabled={isStreaming || !!pendingToolCall}
              />

              <button
                type="submit"
                disabled={!input.trim() || isStreaming || !!pendingToolCall}
                className="p-3 shrink-0 rounded-xl bg-[var(--hey-primary)] text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity mr-1 mb-1"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
            
          </div>
        </div>
      </div>

      <TraceDrawer 
        open={drawerOpen} 
        onOpenChange={setDrawerOpen} 
        message={selectedMessage}
      />
    </>
  );
}
