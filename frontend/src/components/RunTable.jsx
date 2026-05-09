import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import StatusBadge from './StatusBadge'

function relTime(iso) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60_000) return 'just now'
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)}h ago`
  return new Date(iso).toLocaleDateString()
}

function duration(start, end) {
  if (!start || !end) return '—'
  const ms = new Date(end) - new Date(start)
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const td = { padding: '10px 12px', fontSize: 13, borderBottom: '1px solid var(--border)', verticalAlign: 'top' }

// Each run is a single keyed component — renders 1 or 2 <tr> elements safely
function RunRow({ run, expanded, onToggle, showTask }) {
  return (
    <>
      <tr
        style={{ cursor: 'pointer', background: expanded ? 'var(--surface)' : 'transparent' }}
        onClick={() => onToggle(expanded ? null : run.id)}
      >
        <td style={{ ...td, width: 28, color: 'var(--text-muted)' }}>
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </td>
        <td style={td}><StatusBadge status={run.status} /></td>
        {showTask && (
          <td style={{ ...td, fontSize: 12, color: 'var(--text-muted)' }}>{run.task_id?.slice(0, 8)}</td>
        )}
        <td style={{ ...td, fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          {run.triggered_by}
        </td>
        <td style={{ ...td, color: 'var(--text-muted)', fontSize: 12 }}>{relTime(run.started_at)}</td>
        <td style={{ ...td, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
          {duration(run.started_at, run.completed_at)}
        </td>
        <td style={{ ...td, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {run.output || <span style={{ color: 'var(--text-muted)' }}>—</span>}
        </td>
      </tr>

      {expanded && (
        <tr style={{ background: 'var(--surface)' }}>
          <td colSpan={showTask ? 7 : 6} style={{ padding: '0 12px 12px 40px' }}>
            {run.output && (
              <pre style={{
                margin: '8px 0 4px', padding: '10px 12px',
                background: 'var(--surface-2)', borderRadius: 6,
                fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text)',
                whiteSpace: 'pre-wrap', overflowWrap: 'break-word',
              }}>{run.output}</pre>
            )}
            {run.error && (
              <pre style={{
                margin: '4px 0', padding: '10px 12px',
                background: 'rgba(224,84,84,0.1)', borderRadius: 6,
                border: '1px solid rgba(224,84,84,0.3)',
                fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--error)',
                whiteSpace: 'pre-wrap', overflowWrap: 'break-word',
              }}>{run.error}</pre>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

export default function RunTable({ runs = [], showTask = false }) {
  const [expanded, setExpanded] = useState(null)

  if (!runs.length) return (
    <p style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '32px 0' }}>
      No runs yet.
    </p>
  )

  const th = {
    fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.06em',
    padding: '8px 12px', textAlign: 'left', borderBottom: '1px solid var(--border)',
  }

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          <th style={th} />
          <th style={th}>Status</th>
          {showTask && <th style={th}>Task</th>}
          <th style={th}>Triggered by</th>
          <th style={th}>Started</th>
          <th style={th}>Duration</th>
          <th style={th}>Output</th>
        </tr>
      </thead>
      <tbody>
        {runs.map(run => (
          <RunRow
            key={run.id}
            run={run}
            expanded={expanded === run.id}
            onToggle={setExpanded}
            showTask={showTask}
          />
        ))}
      </tbody>
    </table>
  )
}
