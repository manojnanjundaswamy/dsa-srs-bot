import { useState } from 'react'
import { ChevronDown, ChevronRight, RotateCcw } from 'lucide-react'
import StatusBadge from './StatusBadge'
import ExecutionTimeline from './ExecutionTimeline'

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

function RunRow({ run, expanded, onToggle, showTask, onRetry }) {
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
        <td style={{
          ...td, maxWidth: 220, overflow: 'hidden',
          textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          fontFamily: 'var(--font-mono)', fontSize: 12,
        }}>
          {run.output
            ? run.output
            : run.events?.length
              ? (() => {
                  // Show last meaningful event when there's no print() output
                  const printEv = [...(run.events)].reverse().find(e => e.type === 'print')
                  const lastEv = [...(run.events)].reverse().find(e => e.type !== 'start')
                  const ev = printEv ?? lastEv
                  return ev
                    ? <span style={{ color: 'var(--text-muted)' }}>{ev.msg.slice(0, 60)}</span>
                    : <span style={{ color: 'var(--text-muted)' }}>—</span>
                })()
              : <span style={{ color: 'var(--text-muted)' }}>—</span>
          }
        </td>
        {/* Retry on failed runs */}
        <td style={{ ...td, width: 36 }} onClick={e => e.stopPropagation()}>
          {run.status === 'failed' && onRetry && (
            <button
              title="Retry this task"
              onClick={() => onRetry(run.task_id)}
              style={{
                width: 26, height: 26, display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: 'rgba(224,84,84,0.1)', border: '1px solid rgba(224,84,84,0.3)',
                borderRadius: 4, color: 'var(--error)', cursor: 'pointer',
              }}
            >
              <RotateCcw size={12} />
            </button>
          )}
        </td>
      </tr>

      {expanded && (
        <tr style={{ background: 'var(--surface)' }}>
          <td colSpan={showTask ? 8 : 7} style={{ padding: 0 }}>
            {/* Structured execution timeline (if events available) */}
            {run.events && run.events.length > 0 ? (
              <ExecutionTimeline events={run.events} />
            ) : (
              /* Fallback: plain output + error */
              <div style={{ padding: '8px 12px 12px 40px' }}>
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
                {!run.output && !run.error && (
                  <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>No output recorded.</p>
                )}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  )
}

export default function RunTable({ runs = [], showTask = false, onRetry }) {
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
          <th style={th} />
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
            onRetry={onRetry}
          />
        ))}
      </tbody>
    </table>
  )
}
