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
      <div className="p-4 border-b border-gray-100 bg-white/80 backdrop-blur-md sticky top-0 z-10 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-2">
            <UserIcon className="w-4 h-4 text-[var(--hey-primary)]" />
            Client Profile
          </h2>
          <p className="text-xs text-gray-500 mt-1 font-medium">
            Perspectiva 360° en tiempo real
          </p>
        </div>
      </div>
      
      <ScrollArea className="flex-1 p-6">
        <div className="space-y-6 pb-10">
          
          {/* Main User Info */}
          <div className="flex flex-col items-center justify-center p-6 rounded-3xl bg-white shadow-md text-center border-0">
            <div 
              className="w-20 h-20 rounded-full flex items-center justify-center text-2xl font-extrabold text-[var(--hey-primary)] shadow-sm mb-4"
              style={{ background: 'linear-gradient(135deg, #e6f9f0 0%, #c1f0db 100%)' }}
            >
              {user.name.charAt(0)}
            </div>
            <h3 className="font-extrabold text-xl text-foreground">{user.name}</h3>
            <p className="text-sm text-gray-500 font-medium mt-1">{user.id}</p>
          </div>

          {!ficha ? (
            <>
              <SkeletonCard title="Perfil Conductual" />
              <SkeletonCard title="Top Gastos" />
              <SkeletonCard title="Salud Financiera" />
            </>
          ) : (
            <>
              <BehavioralCard ficha={ficha} color={(user as any).color || '#00C389'} />
              <TransactionalCard ficha={ficha} />
              <HealthCard ficha={ficha} />
            </>
          )}

        </div>
      </ScrollArea>
    </div>
  );
}
