import { User, ClientFicha } from '../../types';
import { ScrollArea } from '../ui/scroll-area';
import { SkeletonCard } from './SkeletonCard';
import { BehavioralCard } from './BehavioralCard';
import { TransactionalCard } from './TransactionalCard';
import { HealthCard } from './HealthCard';
import { User as UserIcon } from 'lucide-react';

interface ProfilePanelProps {
  user: User;
  ficha: ClientFicha | null;
}

export function ProfilePanel({ user, ficha }: ProfilePanelProps) {
  return (
    <div className="h-full flex flex-col bg-card">
      <div className="p-4 border-b border-border bg-background/50 backdrop-blur-sm sticky top-0 z-10 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-foreground flex items-center gap-2">
            <UserIcon className="w-4 h-4 text-[var(--hey-primary)]" />
            Client Profile
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Perspectiva 360° en tiempo real
          </p>
        </div>
      </div>
      
      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6 pb-10">
          
          {/* Main User Info */}
          <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-border bg-background shadow-sm text-center">
            <div 
              className="w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold text-white shadow-inner mb-3"
              style={{ backgroundColor: user.color }}
            >
              {user.name.charAt(0)}
            </div>
            <h3 className="font-bold text-lg text-foreground">{user.name}</h3>
            <p className="text-xs text-muted-foreground">{user.id}</p>
          </div>

          {!ficha ? (
            <>
              <SkeletonCard title="Perfil Conductual" />
              <SkeletonCard title="Top Gastos" />
              <SkeletonCard title="Salud Financiera" />
            </>
          ) : (
            <>
              <BehavioralCard ficha={ficha} color={user.color} />
              <TransactionalCard ficha={ficha} />
              <HealthCard ficha={ficha} />
            </>
          )}

        </div>
      </ScrollArea>
    </div>
  );
}
