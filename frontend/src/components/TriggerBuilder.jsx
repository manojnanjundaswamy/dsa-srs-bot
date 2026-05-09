import { useState } from 'react'
import { Clock, Timer, Webhook, Play } from 'lucide-react'

const CRON_PRESETS = [
  { label: 'Daily 7 AM (IST)',  value: '0 7 * * *' },
  { label: 'Daily 3 PM (IST)',  value: '0 15 * * *' },
  { label: 'Daily 10 PM (IST)', value: '0 22 * * *' },
  { label: 'Monday 9 AM (IST)', value: '0 9 * * 1' },
  { label: 'Custom',            value: 'custom' },
]

const INTERVAL_UNITS = [
  { label: 'seconds', factor: 1 },
  { label: 'minutes', factor: 60 },
  { label: 'hours',   factor: 3600 },
]

function decomposeInterval(seconds) {
  // Try largest unit first (hours → minutes → seconds)
  const units = [
    { label: 'hours',   factor: 3600 },
    { label: 'minutes', factor: 60 },
    { label: 'seconds', factor: 1 },
  ]
  for (const u of units) {
    if (seconds >= u.factor && seconds % u.factor === 0) {
      return { num: seconds / u.factor, unit: u.label }
    }
  }
  return { num: seconds, unit: 'seconds' }
}

export default function TriggerBuilder({ type, config, onChange, onTypeChange }) {
  // Initialize cron preset by matching against saved expression
  const savedCron = config?.cron ?? ''
  const matchedPreset = CRON_PRESETS.find(p => p.value !== 'custom' && p.value === savedCron)
  const [cronPreset, setCronPreset] = useState(matchedPreset ? matchedPreset.value : 'custom')

  // Decompose interval_seconds into a human-readable num + unit
  const { num: initNum, unit: initUnit } = config?.interval_seconds
    ? decomposeInterval(config.interval_seconds)
    : { num: 10, unit: 'seconds' }
  const [intervalNum, setIntervalNum] = useState(initNum)
  const [intervalUnit, setIntervalUnit] = useState(initUnit)

  const TYPES = [
    { id: 'cron',     icon: Clock,   label: 'Cron' },
    { id: 'interval', icon: Timer,   label: 'Interval' },
    { id: 'event',    icon: Webhook, label: 'Event' },
    { id: 'manual',   icon: Play,    label: 'Manual' },
  ]

  const inp = (style = {}) => ({
    background: 'var(--surface-2)',
    border: '1px solid var(--border)',
    borderRadius: 6, color: 'var(--text)',
    padding: '8px 12px', fontSize: 13,
    fontFamily: 'var(--font-ui)', width: '100%',
    ...style,
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Type selector */}
      <div style={{ display: 'flex', gap: 8 }}>
        {TYPES.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            type="button"
            onClick={() => onTypeChange(id)}
            style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', gap: 6,
              padding: '10px 8px', borderRadius: 6,
              border: `1px solid ${type === id ? 'var(--accent)' : 'var(--border)'}`,
              background: type === id ? 'var(--accent-dim)' : 'var(--surface-2)',
              color: type === id ? 'var(--accent)' : 'var(--text-muted)',
              cursor: 'pointer', fontSize: 11, fontWeight: 500,
              transition: 'all 0.15s',
            }}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Cron config */}
      {type === 'cron' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {CRON_PRESETS.map(p => (
              <button
                key={p.value}
                type="button"
                onClick={() => {
                  setCronPreset(p.value)
                  if (p.value !== 'custom') {
                    onChange({ cron: p.value, timezone: config?.timezone ?? 'Asia/Kolkata' })
                  }
                }}
                style={{
                  padding: '4px 10px', borderRadius: 4, fontSize: 12,
                  border: `1px solid ${cronPreset === p.value ? 'var(--accent)' : 'var(--border)'}`,
                  background: cronPreset === p.value ? 'var(--accent-dim)' : 'transparent',
                  color: cronPreset === p.value ? 'var(--accent)' : 'var(--text-muted)',
                  cursor: 'pointer',
                }}
              >
                {p.label}
              </button>
            ))}
          </div>
          <input
            style={{ ...inp(), fontFamily: 'var(--font-mono)' }}
            placeholder="cron expression: 0 7 * * *"
            value={config?.cron ?? ''}
            onChange={e => {
              setCronPreset('custom')
              onChange({ cron: e.target.value, timezone: config?.timezone ?? 'Asia/Kolkata' })
            }}
          />
          <select
            style={inp()}
            value={config?.timezone ?? 'Asia/Kolkata'}
            onChange={e => onChange({ ...config, timezone: e.target.value })}
          >
            {['Asia/Kolkata', 'UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo'].map(tz => (
              <option key={tz} value={tz}>{tz}</option>
            ))}
          </select>
        </div>
      )}

      {/* Interval config */}
      {type === 'interval' && (
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="number" min={1}
            style={{ ...inp(), width: 100 }}
            value={intervalNum}
            onChange={e => {
              const n = parseInt(e.target.value) || 1
              setIntervalNum(n)
              const unit = INTERVAL_UNITS.find(u => u.label === intervalUnit)
              onChange({ interval_seconds: n * (unit?.factor ?? 1) })
            }}
          />
          <select
            style={{ ...inp(), width: 120 }}
            value={intervalUnit}
            onChange={e => {
              setIntervalUnit(e.target.value)
              const unit = INTERVAL_UNITS.find(u => u.label === e.target.value)
              onChange({ interval_seconds: intervalNum * (unit?.factor ?? 1) })
            }}
          >
            {INTERVAL_UNITS.map(u => <option key={u.label} value={u.label}>{u.label}</option>)}
          </select>
          <span style={{ color: 'var(--text-muted)', fontSize: 12, alignSelf: 'center' }}>
            = {config?.interval_seconds ?? intervalNum}s
          </span>
        </div>
      )}

      {/* Event config */}
      {type === 'event' && (
        <input
          style={inp()}
          placeholder="event_key (e.g. telegram_update)"
          value={config?.event_key ?? ''}
          onChange={e => onChange({ event_key: e.target.value })}
        />
      )}

      {/* Manual */}
      {type === 'manual' && (
        <p style={{ color: 'var(--text-muted)', fontSize: 12, margin: 0 }}>
          Triggered manually via the Run Now button or API only.
        </p>
      )}
    </div>
  )
}
