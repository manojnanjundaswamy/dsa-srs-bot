import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Pencil, Play, Copy, Trash2, ChevronLeft, Loader2 } from 'lucide-react'
import { getTask, getTaskRuns, runTask, enableTask, disableTask, duplicateTask, deleteTask } from '../api/client'
import TypeBadge from '../components/TypeBadge'
import StatusBadge from '../components/StatusBadge'
import ScriptEditor from '../components/ScriptEditor'
import RunTable from '../components/RunTable'
import { useToast } from '../components/Toast'

function fmtDate(iso) {
  return iso ? new Date(iso).toLocaleString('en-IN') : '—'
}

const MetaRow = ({ label, children }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
    <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{label}</span>
    <span style={{ fontSize: 13 }}>{children}</span>
  </div>
)

export default function TaskDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const toast = useToast()
  const [running, setRunning] = useState(false)

  const { data: task, isLoading } = useQuery({ queryKey: ['task', id], queryFn: () => getTask(id) })
  const { data: runs = [], refetch: refetchRuns } = useQuery({
    queryKey: ['runs', id],
    queryFn: () => getTaskRuns(id, { limit: 50 }),
    enabled: !!id,
    refetchInterval: 10_000,
  })

  const qc_inv = () => {
    qc.invalidateQueries({ queryKey: ['task', id] })
    qc.invalidateQueries({ queryKey: ['tasks'] })
    qc.invalidateQueries({ queryKey: ['all-runs'] })
  }

  const toggleMut = useMutation({
    mutationFn: () => task?.enabled ? disableTask(id) : enableTask(id),
    onSuccess: () => { qc_inv(); toast(task?.enabled ? 'Task disabled' : 'Task enabled', 'success') },
    onError: (e) => toast(e.message, 'error'),
  })

  const dupMut = useMutation({
    mutationFn: () => duplicateTask(id),
    onSuccess: (copy) => { toast(`Duplicated as "${copy.name}"`, 'success'); navigate(`/tasks/${copy.id}`) },
    onError: (e) => toast(e.message, 'error'),
  })

  const delMut = useMutation({
    mutationFn: () => deleteTask(id),
    onSuccess: () => { toast('Task deleted', 'info'); navigate('/tasks') },
    onError: (e) => toast(e.message, 'error'),
  })

  const handleRun = async () => {
    setRunning(true)
    try {
      const run = await runTask(id)
      refetchRuns()
      qc_inv()
      toast(`Run ${run.status}`, run.status === 'success' ? 'success' : 'error')
    } catch (e) {
      toast(e.message, 'error')
    } finally {
      setRunning(false)
    }
  }

  if (isLoading) return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80, color: 'var(--text-muted)' }}>
      <Loader2 size={24} style={{ animation: 'spin 1s linear infinite' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )

  if (!task) return <p style={{ color: 'var(--error)' }}>Task not found.</p>

  const btnStyle = (color = 'var(--text-muted)') => ({
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '7px 12px', borderRadius: 6,
    background: 'var(--surface-2)', border: '1px solid var(--border)',
    color, cursor: 'pointer', fontSize: 12, fontWeight: 500,
  })

  const trigger = task.trigger_config ?? {}

  return (
    <div style={{ maxWidth: 960 }}>
      {/* Back + header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 28 }}>
        <button onClick={() => navigate('/tasks')} style={{ ...btnStyle(), marginTop: 6, flexShrink: 0 }}>
          <ChevronLeft size={14} /> Back
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h1 style={{ margin: 0, fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 24, color: 'var(--text)' }}>
              {task.name}
            </h1>
            <TypeBadge type={task.type} />
            {!task.enabled && <StatusBadge status="disabled" />}
          </div>
          {task.description && (
            <p style={{ margin: '6px 0 0', fontSize: 13, color: 'var(--text-muted)' }}>{task.description}</p>
          )}
        </div>
        {/* Actions */}
        <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
          <button onClick={handleRun} disabled={running} style={btnStyle('var(--success)')}>
            {running ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={13} />}
            Run Now
          </button>
          <button onClick={() => navigate(`/tasks/${id}/edit`)} style={btnStyle()}>
            <Pencil size={13} /> Edit
          </button>
          <button onClick={() => toggleMut.mutate()} style={btnStyle()}>
            {task.enabled ? 'Disable' : 'Enable'}
          </button>
          <button onClick={() => dupMut.mutate()} style={btnStyle()}>
            <Copy size={13} /> Duplicate
          </button>
          <button onClick={() => { if (confirm(`Delete "${task.name}"?`)) delMut.mutate() }} style={btnStyle('var(--error)')}>
            <Trash2 size={13} /> Delete
          </button>
        </div>
      </div>

      {/* Two-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20, marginBottom: 32 }}>
        {/* Left: meta */}
        <div style={{
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 8, padding: '20px', display: 'flex', flexDirection: 'column', gap: 16,
        }}>
          <MetaRow label="Type"><TypeBadge type={task.type} /></MetaRow>

          <MetaRow label="Trigger">
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
              {trigger.cron ?? (trigger.interval_seconds ? `every ${trigger.interval_seconds}s` : trigger.event_key ?? task.type)}
            </span>
            {trigger.timezone && <span style={{ color: 'var(--text-muted)', fontSize: 11, display: 'block' }}>{trigger.timezone}</span>}
          </MetaRow>

          <MetaRow label="Last run">{fmtDate(task.last_run_at)}</MetaRow>
          <MetaRow label="Created">{fmtDate(task.created_at)}</MetaRow>
          <MetaRow label="Updated">{fmtDate(task.updated_at)}</MetaRow>

          {task.parent_task_id && (
            <MetaRow label="Duplicated from">
              <button onClick={() => navigate(`/tasks/${task.parent_task_id}`)}
                style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, padding: 0 }}>
                {task.parent_task_id.slice(0, 12)}…
              </button>
            </MetaRow>
          )}

          {Object.keys(task.script_args ?? {}).length > 0 && (
            <MetaRow label="Args">
              {Object.entries(task.script_args).map(([k, v]) => (
                <div key={k} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                  <span style={{ color: 'var(--accent)' }}>{k}</span>: {String(v)}
                </div>
              ))}
            </MetaRow>
          )}

          {task.prompt && (
            <MetaRow label="Prompt">
              <span style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic' }}>"{task.prompt}"</span>
            </MetaRow>
          )}
        </div>

        {/* Right: script */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Script</span>
            <button onClick={() => navigate(`/tasks/${id}/edit`)} style={{ fontSize: 11, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
              Edit →
            </button>
          </div>
          <ScriptEditor value={task.script} readOnly minHeight={280} />
        </div>
      </div>

      {/* Run history */}
      <div>
        <h2 style={{ fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: 17, color: 'var(--text)', margin: '0 0 12px' }}>
          Run History
          <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
            {runs.length} run{runs.length !== 1 ? 's' : ''}
          </span>
        </h2>
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
          <RunTable runs={runs} />
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
