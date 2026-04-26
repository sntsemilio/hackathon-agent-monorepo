import { ActionCardData } from '../../types';
import { motion } from 'framer-motion';
import { ChevronRight, ExternalLink } from 'lucide-react';
import { useState } from 'react';
import { ActionModal } from '../modals/ActionModal';

interface ActionCardProps {
  card: ActionCardData;
}

export function ActionCard({ card }: ActionCardProps) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setModalOpen(true)}
        className="flex items-center justify-between p-4 rounded-2xl border-0 bg-white hover:bg-gray-50 cursor-pointer transition-all shadow-sm hover:shadow-md"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[var(--hey-primary)]/10 flex items-center justify-center text-[var(--hey-primary)]">
            <ExternalLink className="w-4 h-4" />
          </div>
          <span className="font-medium text-sm text-foreground">{card.title}</span>
        </div>
        
        <div className="flex items-center gap-1 text-xs font-semibold text-[var(--hey-primary)]">
          {card.cta}
          <ChevronRight className="w-3.5 h-3.5" />
        </div>
      </motion.div>

      <ActionModal 
        open={modalOpen} 
        onOpenChange={setModalOpen} 
        card={card} 
      />
    </>
  );
}
