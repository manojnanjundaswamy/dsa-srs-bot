import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Play, Pencil, Copy, Trash2, Plus, Loader2 } from 'lucide-react'
import { getTasks, runTask, enableTask, disableTask, duplicateTask, deleteTask, getSchedulerStatus } from '../api/client'
import StatusBadge from '../components/StatusBadge'
import TypeBadge from '../components/TypeBadge'
import { useToast } from '../components/Toast'

function relTime(iso) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60_000) return 'just now'
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)}h ago`
  return new Date(iso).toLocaleDateString()
}

function fmtNext(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const FILTERS = ['all', 'cron', 'interval', 'event', 'manual']

export default function TaskList() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const toast = useToast()
  const [typeFilter, setTypeFilter] = useState('all')
  const [runningId, setRunningId] = useState(null)

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => getTasks(),
    refetchInterval: 20_000,
  })

  const { data: schedStatus } = useQuery({
    queryKey: ['scheduler-status'],
    queryFn: getSchedulerStatus,
    refetchInterval: 15_000,
  })

  // Map task_id → scheduler job for quick next_run_time lookup
  const jobMap = new Map((schedStatus?.jobs ?? []).map(j => [j.task_id, j]))

  const filtered = typeFilter === 'all' ? tasks : tasks.filter(t => t.type === typeFilter)

  const toggleMut = useMutation({
    mutationFn: ({ id, enabled }) => enabled ? disableTask(id) : enableTask(id),
    onSuccess: (_, { enabled }) => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['scheduler-status'] })
      toast(enabled ? 'Task disabled' : 'Task enabled', 'success')
    },
    onError: (e) => toast(e.message, 'error'),
  })

  const dupMut = useMutation({
    mutationFn: duplicateTask,
    onSuccess: (copy) => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      toast(`Duplicated — "${copy.name}" created (disabled)`, 'success')
    },
    onError: (e) => toast(e.message, 'error'),
  })

  const delMut = useMutation({
    mutationFn: deleteTask,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      toast('Task deleted', 'info')
    },
    onError: (e) => toast(e.message, 'error'),
  })

  const handleRun = async (id, name) => {
    setRunningId(id)
    try {
      const run = await runTask(id)
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['all-runs'] })
      toast(`"${name}" ran — ${run.status}`, run.status === 'success' ? 'success' : 'error')
    } catch (e) {
      toast(e.message, 'error')
    } finally {
      setRunningId(null)
    }
  }

  const th = {
    fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.06em',
    padding: '10px 16px', textAlign: 'left', borderBottom: '1px solid var(--border)',
    whiteSpace: 'nowrap',
  }

  const td = { padding: '12px 16px', fontSize: 13, borderBottom: '1px solid var(--border)', verticalAlign: 'middle' }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 26, color: 'var(--text)' }}>Tasks</h1>
          <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-muted)' }}>{tasks.length} task{tasks.length !== 1 ? 's' : ''} total</p>
        </div>
        <button
          onClick={() => navigate('/tasks/new')}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '9px 16px', borderRadius: 6,
            background: 'var(--accent)', border: 'none',
            color: '#111', fontWeight: 600, fontSize: 13, cursor: 'pointer',
          }}
        >
          <Plus size={14} /> New Task
        </button>
      </div>

      {/* Filter bar */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
        {FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setTypeFilter(f)}
            style={{
              padding: '5px 14px', borderRadius: 20, fontSize: 12, fontWeight: 500,
              border: `1px solid ${typeFilter === f ? 'var(--accent)' : 'var(--border)'}`,
              background: typeFilter === f ? 'var(--accent-dim)' : 'transparent',
              color: typeFilter === f ? 'var(--accent)' : 'var(--text-muted)',
              cursor: 'pointer', textTransform: 'capitalize',
            }}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Table */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
        {isLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0', color: 'var(--text-muted)' }}>
            <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        ) : filtered.length === 0 ? (
          <p style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-muted)', fontSize: 13 }}>
            No tasks found. <button onClick={() => navigate('/tasks/new')} style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 13 }}>Create one →</button>
          </p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={th}>Name</th>
                <th style={th}>Type</th>
                <th style={th}>Trigger</th>
                <th style={th}>Last run</th>
                <th style={th}>Next run</th>
                <th style={th}>Enabled</th>
                <th style={th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(task => (
                <tr
                  key={task.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/tasks/${task.id}`)}
                >
                  <td style={td}>
                    <div style={{ fontWeight: 500 }}>{task.name}</div>
                    {task.description && (
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{task.description.slice(0, 60)}{task.description.length > 60 ? '…' : ''}</div>
                    )}
                  </td>
                  <td style={td}><TypeBadge type={task.type} /></td>
                  <td style={{ ...td, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-muted)' }}>
                    {task.trigger_config?.cron ?? task.trigger_config?.interval_seconds
                      ? (task.trigger_config.cron ?? `${task.trigger_config.interval_seconds}s`)
                      : task.type}
                  </td>
                  <td style={{ ...td, fontSize: 12, color: 'var(--text-muted)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {task.last_run_status && (
                        <span style={{
                          width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                          background: task.last_run_status === 'success' ? 'var(--success)' : 'var(--error)',
                        }} />
                      )}
                      {relTime(task.last_run_at)}
                    </div>
                  </td>
                  <td style={{ ...td, fontSize: 12, color: 'var(--text-muted)' }}>
                    {fmtNext(jobMap.get(task.id)?.next_run_time)}
                  </td>
                  <td style={td} onClick={e => e.stopPropagation()}>
                    {(() => {
                      const isToggling = toggleMut.isPending && toggleMut.variables?.id === task.id
                      return (
                        <div
                          onClick={() => !isToggling && toggleMut.mutate({ id: task.id, enabled: task.enabled })}
                          style={{
                            width: 36, height: 20, borderRadius: 10,
                            cursor: isToggling ? 'not-allowed' : 'pointer',
                            opacity: isToggling ? 0.5 : 1,
                            background: task.enabled ? 'var(--accent)' : 'var(--surface-2)',
                            border: `1px solid ${task.enabled ? 'var(--accent)' : 'var(--border)'}`,
                            position: 'relative', transition: 'all 0.2s',
                          }}
                        >
                          <div style={{
                            width: 14, height: 14, borderRadius: '50%', background: '#fff',
                            position: 'absolute', top: 2, left: task.enabled ? 18 : 2, transition: 'left 0.2s',
                          }} />
                        </div>
                      )
                    })()}
                  </td>
                  <td style={td} onClick={e => e.stopPropagation()}>
                    <div style={{ display: 'flex', gap: 4 }}>
                      {[
                        {
                          icon: runningId === task.id ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={13} />,
                          title: 'Run now',
                          onClick: () => handleRun(task.id, task.name),
                          color: 'var(--success)',
                        },
                        { icon: <Pencil size={13} />, title: 'Edit', onClick: () => navigate(`/tasks/${task.id}/edit`), color: 'var(--text-muted)' },
                        { icon: <Copy size={13} />, title: 'Duplicate', onClick: () => dupMut.mutate(task.id), color: 'var(--text-muted)' },
                        {
                          icon: <Trash2 size={13} />, title: 'Delete',
                          onClick: () => { if (confirm(`Delete "${task.name}"?`)) delMut.mutate(task.id) },
                          color: 'var(--error)',
                        },
                      ].map(({ icon, title, onClick, color }) => (
                        <button
                          key={title}
                          title={title}
                          onClick={onClick}
                          style={{
                            width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 4,
                            color, cursor: 'pointer',
                          }}
                        >
                          {icon}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
