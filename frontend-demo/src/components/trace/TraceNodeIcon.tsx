import { NODE_ICONS, NODE_TONES, TONE_STYLES } from './tokens'

interface TraceNodeIconProps {
  node: string
  status: 'pending' | 'running' | 'done' | 'error'
}

export function TraceNodeIcon({ node, status }: TraceNodeIconProps) {
  const tone = NODE_TONES[node] || 'neutral'
  const style = TONE_STYLES[tone]
  const IconComponent = NODE_ICONS[node]

  return (
    <div
      className="shrink-0 relative flex items-center justify-center"
      style={{
        width: 28,
        height: 28,
        borderRadius: 8,
        background: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
      }}
    >
      {IconComponent ? (
        <IconComponent size={14} strokeWidth={2} />
      ) : (
        <span style={{ fontSize: 12, fontWeight: 600 }}>{node.substring(0, 3).toUpperCase()}</span>
      )}

      {status === 'running' && (
        <div
          style={{
            position: 'absolute',
            top: -2,
            right: -2,
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: '#FF8C42',
            border: '2px solid #FFFFFF',
            animation: 'pulse 1.6s infinite',
          }}
        />
      )}
    </div>
  )
}
