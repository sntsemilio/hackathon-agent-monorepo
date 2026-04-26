import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface SkeletonCardProps {
  title: string;
}

export function SkeletonCard({ title }: SkeletonCardProps) {
  return (
    <Card className="bg-white border-0 shadow-md rounded-3xl overflow-hidden relative">
      {/* Animated shimmer overlay */}
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-gray-100/50 to-transparent z-10" />
      
      <CardHeader className="p-5 pb-2">
        <CardTitle className="text-sm font-bold text-gray-400">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-4 pt-2 space-y-4">
        {/* Placeholder Shapes */}
        <div className="w-full h-32 rounded-full bg-muted/50 mx-auto" style={{ width: '120px' }} />
        <div className="space-y-2">
          <div className="h-2 rounded bg-muted/50 w-3/4 mx-auto" />
          <div className="h-2 rounded bg-muted/50 w-1/2 mx-auto" />
        </div>
      </CardContent>
    </Card>
  );
}
