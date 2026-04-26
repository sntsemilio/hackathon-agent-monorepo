import { ToolCallIntent } from '../../types';
import { Button } from '../ui/button';
import { Check, X, ShieldAlert } from 'lucide-react';

interface ConfirmationCardProps {
  toolCall: ToolCallIntent;
  onConfirm: (confirmed: boolean) => void;
}

export function ConfirmationCard({ toolCall, onConfirm }: ConfirmationCardProps) {
  return (
    <div className="w-full max-w-sm rounded-xl border border-yellow-500/30 bg-card overflow-hidden shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-300">
      
      {/* Header */}
      <div className="bg-yellow-500/10 px-4 py-3 flex items-center gap-2 border-b border-yellow-500/20">
        <ShieldAlert className="w-4 h-4 text-yellow-500" />
        <span className="font-semibold text-sm text-foreground">Autorización Requerida</span>
      </div>

      {/* Body */}
      <div className="p-4 space-y-3">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Acción</p>
          <p className="text-sm font-medium">{toolCall.description || toolCall.tool_name}</p>
        </div>

        {Object.keys(toolCall.params).length > 0 && (
          <div className="bg-muted/50 rounded-lg p-3 border border-border">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold mb-2">Parámetros</p>
            <dl className="space-y-1.5">
              {Object.entries(toolCall.params).map(([key, val]) => (
                <div key={key} className="flex flex-col sm:flex-row sm:justify-between text-xs">
                  <dt className="text-muted-foreground font-mono">{key}:</dt>
                  <dd className="font-medium text-foreground text-right">{String(val)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 bg-muted/30 border-t border-border flex gap-2 justify-end">
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => onConfirm(false)}
          className="border-red-500/30 hover:bg-red-500/10 hover:text-red-500 text-muted-foreground"
        >
          <X className="w-4 h-4 mr-1.5" />
          Cancelar
        </Button>
        <Button 
          variant="default" 
          size="sm" 
          onClick={() => onConfirm(true)}
          className="bg-[var(--hey-primary)] hover:bg-[var(--hey-primary)]/90 text-white"
        >
          <Check className="w-4 h-4 mr-1.5" />
          Confirmar
        </Button>
      </div>
    </div>
  );
}
