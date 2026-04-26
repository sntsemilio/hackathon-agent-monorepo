import { STATUS_BADGE, TraceStatus } from './tokens'

interface TraceStatusBadgeProps {
  status: TraceStatus
}

export function TraceStatusBadge({ status }: TraceStatusBadgeProps) {
  const badge = STATUS_BADGE[status]

  return (
    <span
      className="inline-flex items-center font-semibold uppercase shrink-0"
      style={{
        height: 18,
        padding: '0 6px',
        fontSize: 9.5,
        letterSpacing: '0.04em',
        background: badge.bg,
        color: badge.color,
        borderRadius: '9999px',
      }}
    >
      {status === 'running' && (
        <div
          style={{
            width: 4,
            height: 4,
            borderRadius: '50%',
            background: 'currentColor',
            marginRight: 4,
            animation: 'pulse 1.2s infinite',
          }}
        />
      )}
      {badge.label}
    </span>
  )
}
