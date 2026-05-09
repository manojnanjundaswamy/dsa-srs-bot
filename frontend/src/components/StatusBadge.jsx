const STATUS = {
  success:  { color: 'var(--success)', label: 'Success' },
  failed:   { color: 'var(--error)',   label: 'Failed'  },
  running:  { color: 'var(--running)', label: 'Running' },
  disabled: { color: 'var(--text-muted)', label: 'Disabled' },
}

export default function StatusBadge({ status, size = 'sm' }) {
  const s = STATUS[status] ?? STATUS.disabled
  const pad = size === 'sm' ? '2px 8px' : '4px 12px'
  const fs = size === 'sm' ? 11 : 12

  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: pad, borderRadius: 20,
      background: s.color + '18',
      border: `1px solid ${s.color}44`,
      fontSize: fs, fontWeight: 500, color: s.color,
      whiteSpace: 'nowrap',
    }}>
      <span style={{
        width: 5, height: 5, borderRadius: '50%',
        background: s.color,
        animation: status === 'running' ? 'pulse 1.4s infinite' : 'none',
      }} />
      {s.label}
    </span>
  )
}
