import { ActionCardData } from '../../types';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Button } from '../ui/button';
import { ExternalLink } from 'lucide-react';

interface ActionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  card: ActionCardData;
}

export function ActionModal({ open, onOpenChange, card }: ActionModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-card border border-border">
        <DialogHeader>
          <div className="w-12 h-12 rounded-full bg-[var(--hey-primary)]/10 flex items-center justify-center text-[var(--hey-primary)] mb-4 mx-auto">
            <ExternalLink className="w-6 h-6" />
          </div>
          <DialogTitle className="text-center">{card.title}</DialogTitle>
          <DialogDescription className="text-center pt-2">
            En la app real de Hey Banco, esta acción te llevaría a la sección de:
          </DialogDescription>
        </DialogHeader>
        
        <div className="bg-muted p-4 rounded-lg my-4 flex items-center justify-center">
          <code className="text-sm text-[var(--hey-primary)] font-mono">{card.deep_link}</code>
        </div>
        
        <div className="flex justify-center">
          <Button onClick={() => onOpenChange(false)} className="bg-[var(--hey-primary)] hover:bg-[var(--hey-primary)]/90 text-white w-full sm:w-auto">
            Entendido
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
