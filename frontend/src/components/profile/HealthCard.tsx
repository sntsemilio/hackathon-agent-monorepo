import { ClientFicha } from '../../types';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { motion } from 'framer-motion';

interface HealthCardProps {
  ficha: ClientFicha;
}

export function HealthCard({ ficha }: HealthCardProps) {
  const score = ficha.health_score || 0;
  
  // Calculate color and rotation based on score (0-100)
  // Red (0) -> Yellow (50) -> Green (100)
  let color = 'var(--destructive)';
  if (score > 70) color = 'var(--hey-primary)';
  else if (score > 40) color = '#eab308'; // yellow-500

  // 180 degrees total (semi-circle)
  const rotation = (score / 100) * 180;

  return (
    <motion.div
      initial={{ rotateY: 90, opacity: 0 }}
      animate={{ rotateY: 0, opacity: 1 }}
      transition={{ duration: 0.6, type: 'spring', bounce: 0.4, delay: 0.2 }}
    >
      <Card className="border-border bg-background shadow-sm overflow-hidden">
        <CardHeader className="p-4 pb-0">
          <CardTitle className="text-sm font-semibold text-foreground">Salud Financiera</CardTitle>
        </CardHeader>
        <CardContent className="p-4 flex flex-col items-center justify-center pt-8 pb-6">
          
          {/* Semicircular Gauge */}
          <div className="relative w-40 h-20 overflow-hidden">
            {/* Background Arc */}
            <div className="absolute top-0 left-0 w-40 h-40 rounded-full border-[12px] border-muted" />
            
            {/* Progress Arc */}
            <motion.div 
              className="absolute top-0 left-0 w-40 h-40 rounded-full border-[12px] border-t-transparent border-r-transparent border-b-transparent"
              style={{ borderLeftColor: color }}
              initial={{ rotate: -45 }}
              animate={{ rotate: -45 + rotation }}
              transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
            />
            
            {/* Inner mask to make it a stroke */}
            <div className="absolute top-[12px] left-[12px] w-[136px] h-[136px] rounded-full bg-background" />
            
            {/* Center Text */}
            <div className="absolute bottom-0 left-0 w-full flex flex-col items-center justify-end pb-1">
              <span className="text-3xl font-bold" style={{ color }}>{score}</span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest mt-1">Score</span>
            </div>
          </div>
          
        </CardContent>
      </Card>
    </motion.div>
  );
}
