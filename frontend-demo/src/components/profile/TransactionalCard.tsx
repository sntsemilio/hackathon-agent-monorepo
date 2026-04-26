import { ClientFicha } from '../../types';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';
import { motion } from 'framer-motion';

interface TransactionalCardProps {
  ficha: ClientFicha;
}

export function TransactionalCard({ ficha }: TransactionalCardProps) {
  const categories = ficha.top_categories || [];
  const COLORS = ['#00C389', '#6B4EFF', '#FF8C42', '#EF4444', '#3B82F6'];

  const data = categories.map((cat, idx) => {
    if (typeof cat === 'string') {
      return {
        name: cat,
        amount: Math.floor(Math.random() * 5000) + 500,
        color: COLORS[idx % COLORS.length]
      };
    }
    return {
      name: (cat as any).name || 'Categoría',
      amount: (cat as any).amount || 1000,
      color: (cat as any).color || COLORS[idx % COLORS.length]
    };
  });

  return (
    <motion.div
      initial={{ rotateY: -90, opacity: 0 }}
      animate={{ rotateY: 0, opacity: 1 }}
      transition={{ duration: 0.6, type: 'spring', bounce: 0.4, delay: 0.1 }}
    >
      <Card className="bg-white border-0 shadow-md rounded-3xl overflow-hidden">
        <CardHeader className="p-5 pb-0">
          <CardTitle className="text-sm font-bold text-foreground">Top Gastos (30 días)</CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="h-[160px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={65}
                  paddingAngle={5}
                  dataKey="amount"
                  stroke="none"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip
                  contentStyle={{ backgroundColor: 'var(--card)', borderColor: 'var(--border)', borderRadius: '8px' }}
                  itemStyle={{ color: 'var(--foreground)' }}
                  formatter={(value: any) => [`$${Number(value).toLocaleString()}`, 'Gasto']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-2 mt-2">
            {data.map((cat, idx) => (
              <div key={idx} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: cat.color }} />
                  <span className="text-muted-foreground capitalize">{cat.name}</span>
                </div>
                <span className="font-medium text-foreground">${cat.amount.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
