const TYPE = {
  cron:     { bg: 'rgba(96,170,252,0.12)', border: 'rgba(96,170,252,0.3)', color: 'var(--running)', label: 'Cron' },
  interval: { bg: 'rgba(78,201,148,0.12)', border: 'rgba(78,201,148,0.3)', color: 'var(--success)', label: 'Interval' },
  event:    { bg: 'rgba(232,160,48,0.12)', border: 'rgba(232,160,48,0.3)', color: 'var(--accent)',  label: 'Event' },
  manual:   { bg: 'rgba(125,122,114,0.12)', border: 'rgba(125,122,114,0.3)', color: 'var(--text-muted)', label: 'Manual' },
}

export default function TypeBadge({ type }) {
  const t = TYPE[type] ?? TYPE.manual
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px', borderRadius: 4,
      background: t.bg, border: `1px solid ${t.border}`,
      fontSize: 11, fontWeight: 600, color: t.color,
      fontFamily: 'var(--font-mono)',
      textTransform: 'uppercase', letterSpacing: '0.06em',
    }}>
      {t.label}
    </span>
  )
}
