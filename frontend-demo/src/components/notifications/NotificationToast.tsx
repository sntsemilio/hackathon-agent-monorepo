import { ProactiveInsight } from '../../types';
import { motion, AnimatePresence } from 'framer-motion';
import { X, BellRing } from 'lucide-react';
import { useEffect } from 'react';
import { Button } from '../ui/button';

interface NotificationToastProps {
  notification: ProactiveInsight;
  onDismiss: () => void;
}

export function NotificationToast({ notification, onDismiss }: NotificationToastProps) {
  
  // Auto dismiss after 8 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss();
    }, 8000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20, x: 20 }}
        animate={{ opacity: 1, y: 0, x: 0 }}
        exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
        className="w-80 bg-card border border-[var(--hey-primary)]/30 rounded-xl shadow-lg overflow-hidden pointer-events-auto"
      >
        <div className="bg-[var(--hey-primary)]/10 px-4 py-2.5 flex items-center justify-between border-b border-[var(--hey-primary)]/20">
          <div className="flex items-center gap-2">
            <BellRing className="w-4 h-4 text-[var(--hey-primary)] animate-pulse" />
            <span className="text-xs font-semibold text-[var(--hey-primary)]">Insight Proactivo</span>
          </div>
          <button 
            onClick={onDismiss}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        
        <div className="p-4">
          <h4 className="font-semibold text-sm text-foreground mb-1">{notification.title}</h4>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {notification.body}
          </p>
          
          {notification.action_card && (
            <div className="mt-3 flex justify-end">
              <Button size="sm" variant="secondary" className="h-7 text-xs bg-[var(--hey-primary)] text-white hover:bg-[var(--hey-primary)]/90" onClick={onDismiss}>
                {notification.action_card.title}
              </Button>
            </div>
          )}
        </div>
        
        {/* Progress bar line */}
        <motion.div 
          initial={{ width: '100%' }}
          animate={{ width: 0 }}
          transition={{ duration: 8, ease: "linear" }}
          className="h-0.5 bg-[var(--hey-primary)]"
        />
      </motion.div>
    </AnimatePresence>
  );
}
