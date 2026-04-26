import { ClientFicha } from '../../types';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';

interface BehavioralCardProps {
  ficha: ClientFicha;
  color: string;
}

export function BehavioralCard({ ficha, color }: BehavioralCardProps) {
  const data = [
    { subject: 'Digital', A: ficha.digitalizacion, fullMark: 100 },
    { subject: 'Gasto', A: ficha.gasto, fullMark: 100 },
    { subject: 'Ahorro', A: ficha.ahorro, fullMark: 100 },
    { subject: 'Inversión', A: ficha.inversion, fullMark: 100 },
    { subject: 'Crédito', A: ficha.credito, fullMark: 100 },
  ];

  return (
    <motion.div
      initial={{ rotateY: 90, opacity: 0 }}
      animate={{ rotateY: 0, opacity: 1 }}
      transition={{ duration: 0.6, type: 'spring', bounce: 0.4 }}
    >
      <Card className="bg-white border-0 shadow-md rounded-3xl overflow-hidden">
        <CardHeader className="p-5 pb-0 flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-bold text-foreground">Perfil Conductual</CardTitle>
          <span
            className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border border-border font-bold"
            style={{ color: color, borderColor: `${color}40`, backgroundColor: `${color}10` }}
          >
            {(ficha.segment || 'Cliente').replace(/_/g, ' ')}
          </span>
        </CardHeader>
        <CardContent className="p-2 h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--muted-foreground)', fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
              <Radar
                name="Cliente"
                dataKey="A"
                stroke={color}
                fill={color}
                fillOpacity={0.3}
              />
            </RadarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </motion.div>
  );
}
