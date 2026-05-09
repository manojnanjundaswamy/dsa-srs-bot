export default function StatCard({ label, value, sub, accent }) {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '20px 24px',
      display: 'flex', flexDirection: 'column', gap: 4,
    }}>
      <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        {label}
      </span>
      <span style={{
        fontFamily: 'var(--font-head)', fontWeight: 700,
        fontSize: 36, color: accent ?? 'var(--text)',
        lineHeight: 1,
      }}>
        {value ?? '—'}
      </span>
      {sub && <span style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{sub}</span>}
    </div>
  )
}
