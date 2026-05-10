/**
 * Temporal.io-inspired execution timeline.
 * Renders a run's structured events array as:
 *   - Logs tab: color-coded, timestamped log lines
 *   - Timeline tab: horizontal bar chart with duration bars for API calls
 */

import { useState } from 'react'
import { List, GitBranch } from 'lucide-react'

const EVENT_COLORS = {
  start:    'var(--text-muted)',
  end:      'var(--success)',
  print:    'var(--text)',
  step:     'var(--running)',
  api_call: 'var(--accent)',
  error:    'var(--error)',
}

const EVENT_LABELS = {
  start:    'START',
  end:      'END',
  print:    'OUT',
  step:     'STEP',
  api_call: 'API',
  error:    'ERR',
}

function fmtT(ms) {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

// ── Logs tab ──────────────────────────────────────────────────────────────────

function LogsView({ events }) {
  const [filter, setFilter] = useState('all')
  const types = ['all', ...new Set(events.map(e => e.type))]

  const shown = filter === 'all' ? events : events.filter(e => e.type === filter)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {/* Filter chips */}
      <div style={{ display: 'flex', gap: 6, padding: '8px 0', flexWrap: 'wrap', marginBottom: 6 }}>
        {types.map(t => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            style={{
              padding: '2px 8px', borderRadius: 4, fontSize: 10, fontWeight: 600,
              textTransform: 'uppercase', letterSpacing: '0.06em', cursor: 'pointer',
              border: `1px solid ${filter === t ? (EVENT_COLORS[t] ?? 'var(--accent)') : 'var(--border)'}`,
              background: filter === t ? (EVENT_COLORS[t] ?? 'var(--accent)') + '22' : 'transparent',
              color: filter === t ? (EVENT_COLORS[t] ?? 'var(--accent)') : 'var(--text-muted)',
            }}
          >
            {t === 'all' ? 'ALL' : (EVENT_LABELS[t] ?? t.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Log lines */}
      <div style={{
        background: 'var(--surface-2)', borderRadius: 6,
        border: '1px solid var(--border)',
        maxHeight: 320, overflowY: 'auto',
        fontFamily: 'var(--font-mono)', fontSize: 12,
      }}>
        {shown.length === 0 && (
          <div style={{ padding: 16, color: 'var(--text-muted)', textAlign: 'center' }}>No events.</div>
        )}
        {shown.map((ev, i) => (
          <div
            key={i}
            style={{
              display: 'flex', alignItems: 'flex-start', gap: 10,
              padding: '5px 12px',
              borderBottom: i < shown.length - 1 ? '1px solid var(--border)' : 'none',
            }}
          >
            {/* Timestamp */}
            <span style={{ color: 'var(--text-muted)', flexShrink: 0, fontSize: 11 }}>
              {fmtT(ev.t)}
            </span>
            {/* Type badge */}
            <span style={{
              flexShrink: 0, fontSize: 9, fontWeight: 700,
              textTransform: 'uppercase', letterSpacing: '0.1em',
              color: EVENT_COLORS[ev.type] ?? 'var(--text-muted)',
              width: 32,
            }}>
              {EVENT_LABELS[ev.type] ?? ev.type}
            </span>
            {/* Message */}
            <span style={{
              color: ev.level === 'error' ? 'var(--error)' : ev.type === 'print' ? 'var(--text)' : 'var(--text-muted)',
              flex: 1, wordBreak: 'break-word', lineHeight: 1.4,
            }}>
              {ev.msg}
              {ev.ms != null && (
                <span style={{ color: 'var(--accent)', marginLeft: 6 }}>({fmtT(ev.ms)})</span>
              )}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Timeline tab ──────────────────────────────────────────────────────────────

function TimelineView({ events }) {
  if (!events.length) return (
    <p style={{ color: 'var(--text-muted)', fontSize: 13, padding: '16px 0' }}>No events to display.</p>
  )

  const totalMs = events.length > 0 ? Math.max(...events.map(e => e.t + (e.ms ?? 0)), 1) : 1

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '8px 0' }}>
      {/* Time axis */}
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)',
        paddingLeft: 160, marginBottom: 4,
      }}>
        <span>0</span>
        <span>{fmtT(Math.floor(totalMs / 2))}</span>
        <span>{fmtT(totalMs)}</span>
      </div>

      {/* Event rows */}
      {events.map((ev, i) => {
        const color = EVENT_COLORS[ev.type] ?? 'var(--text-muted)'
        const leftPct = (ev.t / totalMs) * 100
        const widthPct = ev.ms ? Math.max((ev.ms / totalMs) * 100, 0.5) : 0

        return (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, height: 22 }}>
            {/* Label */}
            <div style={{
              width: 152, flexShrink: 0, display: 'flex', gap: 6, alignItems: 'center',
            }}>
              <span style={{
                fontSize: 9, fontWeight: 700, textTransform: 'uppercase',
                color, width: 28, flexShrink: 0,
              }}>
                {EVENT_LABELS[ev.type] ?? ev.type}
              </span>
              <span style={{
                fontSize: 11, color: 'var(--text-muted)', overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1,
              }}>
                {ev.msg.length > 28 ? ev.msg.slice(0, 28) + '…' : ev.msg}
              </span>
            </div>

            {/* Track */}
            <div style={{ flex: 1, position: 'relative', height: 20 }}>
              <div style={{
                position: 'absolute', top: 9, left: 0, right: 0, height: 2,
                background: 'var(--border)',
              }} />

              {/* Duration bar (API calls) */}
              {ev.ms ? (
                <div style={{
                  position: 'absolute', top: 6, height: 8, borderRadius: 3,
                  left: `${leftPct}%`,
                  width: `${widthPct}%`,
                  minWidth: 4,
                  background: color,
                  opacity: 0.85,
                  title: `${fmtT(ev.ms)}`,
                }} />
              ) : (
                /* Instant event dot */
                <div style={{
                  position: 'absolute', top: 7, width: 6, height: 6, borderRadius: '50%',
                  background: color,
                  left: `calc(${leftPct}% - 3px)`,
                }} />
              )}
            </div>

            {/* Duration label */}
            <span style={{
              width: 44, flexShrink: 0, fontSize: 10, fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)', textAlign: 'right',
            }}>
              {ev.ms ? fmtT(ev.ms) : fmtT(ev.t)}
            </span>
          </div>
        )
      })}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ExecutionTimeline({ events = [] }) {
  const [tab, setTab] = useState('logs')

  const tabBtn = (id, icon, label) => (
    <button
      onClick={() => setTab(id)}
      style={{
        display: 'flex', alignItems: 'center', gap: 5,
        padding: '5px 12px', fontSize: 12, fontWeight: 500,
        border: 'none', cursor: 'pointer', borderRadius: 4,
        background: tab === id ? 'var(--accent-dim)' : 'transparent',
        color: tab === id ? 'var(--accent)' : 'var(--text-muted)',
      }}
    >
      {icon} {label}
    </button>
  )

  return (
    <div style={{ padding: '12px 16px 16px', background: 'var(--surface)' }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 10, borderBottom: '1px solid var(--border)', paddingBottom: 6 }}>
        {tabBtn('logs',     <List size={13} />,      'Logs')}
        {tabBtn('timeline', <GitBranch size={13} />, 'Timeline')}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)', alignSelf: 'center' }}>
          {events.length} event{events.length !== 1 ? 's' : ''}
        </span>
      </div>

      {tab === 'logs'     && <LogsView events={events} />}
      {tab === 'timeline' && <TimelineView events={events} />}
    </div>
  )
}
