interface JsonViewProps {
  data?: Record<string, any>
}

export function JsonView({ data }: JsonViewProps) {
  if (!data) return null
  const json = JSON.stringify(data, null, 2)

  return (
    <pre
      className="mt-2 p-2.5 rounded-lg overflow-x-auto"
      style={{
        background: '#0D1117',
        color: '#E2E8F0',
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontSize: '10.5px',
        lineHeight: 1.55,
      }}
    >
      <code>{json}</code>
    </pre>
  )
}
