import { User } from '../types';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { USERS } from '../data/users';

interface TopBarProps {
  selectedUser: User;
  onUserChange: (userId: string) => void;
  personalizationEnabled: boolean;
  onPersonalizationToggle: (enabled: boolean) => void;
}

export function TopBar({ selectedUser, onUserChange, personalizationEnabled, onPersonalizationToggle }: TopBarProps) {
  return (
    <div className="relative z-10 w-full bg-background/80 backdrop-blur-md border-b border-border">
      {/* Accent Line */}
      <div 
        className="absolute top-0 left-0 w-full h-1 transition-colors duration-500 ease-in-out"
        style={{ backgroundColor: selectedUser.color }}
      />
      
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <img src="/hey-banco-logo.svg" alt="Hey Banco" className="h-8 w-auto" />
          </div>
          <div className="h-6 w-px bg-gray-200 mx-2" />
          <span className="text-sm font-bold text-foreground">
            Havi Agent Console
          </span>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Personalización:</span>
            <button 
              onClick={() => onPersonalizationToggle(!personalizationEnabled)}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center justify-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none ${
                personalizationEnabled ? 'bg-[var(--hey-primary)]' : 'bg-muted'
              }`}
            >
              <span className="sr-only">Toggle personalization</span>
              <span 
                className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  personalizationEnabled ? 'translate-x-2' : '-translate-x-2'
                }`}
              />
            </button>
          </div>

          <Select value={selectedUser.id} onValueChange={onUserChange}>
            <SelectTrigger className="w-[280px] bg-white border-0 shadow-sm rounded-full">
              <SelectValue placeholder="Select User" />
            </SelectTrigger>
            <SelectContent className="bg-white border-0 shadow-md rounded-2xl">
              {USERS.map((u) => (
                <SelectItem key={u.id} value={u.id} className="cursor-pointer hover:bg-gray-50 rounded-xl">
                  <div className="flex items-center justify-between w-full">
                    <span className="font-semibold text-foreground">{u.name}</span>
                    <span 
                      className="ml-2 text-xs px-2 py-0.5 rounded-full"
                      style={{ color: u.color, backgroundColor: `${u.color}15` }}
                    >
                      {u.segment.replace(/_/g, ' ')}
                    </span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}
