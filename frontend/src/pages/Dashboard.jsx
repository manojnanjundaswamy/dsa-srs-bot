import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Loader2 } from 'lucide-react'
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getTasks, getSchedulerStatus, getAllRuns, getRunsSummary } from '../api/client'
import StatCard from '../components/StatCard'
import TypeBadge from '../components/TypeBadge'
import StatusBadge from '../components/StatusBadge'

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

export default function Dashboard() {
  const navigate = useNavigate()

  const { data: tasks = [], isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: getTasks,
    refetchInterval: 15_000,
  })

  const { data: schedStatus, isLoading: schedLoading } = useQuery({
    queryKey: ['scheduler-status'],
    queryFn: getSchedulerStatus,
    refetchInterval: 10_000,
  })

  const { data: recentRuns = [] } = useQuery({
    queryKey: ['all-runs'],
    queryFn: () => getAllRuns({ limit: 20 }),
    refetchInterval: 10_000,
  })

  const { data: runsSummary } = useQuery({
    queryKey: ['runs-summary'],
    queryFn: () => getRunsSummary(7),
    refetchInterval: 60_000,
  })

  // Build a task map for quick name lookups in run rows
  const taskMap = new Map(tasks.map(t => [t.id, t]))

  const totalTasks = tasks.length
  const activeTasks = tasks.filter(t => t.enabled).length
  const todayRuns = recentRuns.filter(r => {
    const started = new Date(r.started_at)
    const now = new Date()
    return started.toDateString() === now.toDateString()
  })
  const lastRun = recentRuns[0]

  const scheduledJobs = (schedStatus?.jobs ?? []).filter(j => j.type === 'cron' || j.type === 'interval')

  const isLoading = tasksLoading || schedLoading

  const th = {
    fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.06em',
    padding: '10px 16px', textAlign: 'left', borderBottom: '1px solid var(--border)',
  }
  const td = { padding: '12px 16px', fontSize: 13, borderBottom: '1px solid var(--border)', verticalAlign: 'middle' }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 26, color: 'var(--text)' }}>Dashboard</h1>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-muted)' }}>
          Task Engine overview
        </p>
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 60, color: 'var(--text-muted)' }}>
          <Loader2 size={22} style={{ animation: 'spin 1s linear infinite' }} />
        </div>
      ) : (
        <>
          {/* Stat cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
            <StatCard label="Total Tasks"    value={totalTasks} />
            <StatCard label="Active"         value={activeTasks} accent="var(--success)" />
            <StatCard label="Runs Today"     value={todayRuns.length} accent="var(--running)"
              sub={todayRuns.filter(r => r.status === 'failed').length > 0
                ? `${todayRuns.filter(r => r.status === 'failed').length} failed`
                : 'all ok'} />
            <StatCard
              label="Last Run"
              value={lastRun ? relTime(lastRun.started_at) : '—'}
              sub={lastRun ? taskMap.get(lastRun.task_id)?.name : undefined}
              accent={lastRun?.status === 'failed' ? 'var(--error)' : lastRun ? 'var(--success)' : 'var(--text-muted)'}
            />
          </div>

          {/* Scheduler status banner */}
          <div style={{
            background: schedStatus?.running ? 'rgba(78,201,148,0.08)' : 'rgba(224,84,84,0.08)',
            border: `1px solid ${schedStatus?.running ? 'rgba(78,201,148,0.25)' : 'rgba(224,84,84,0.25)'}`,
            borderRadius: 8, padding: '12px 18px',
            display: 'flex', alignItems: 'center', gap: 10, marginBottom: 28,
          }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: schedStatus?.running ? 'var(--success)' : 'var(--error)',
              animation: schedStatus?.running ? 'pulse 2s infinite' : 'none',
            }} />
            <span style={{ fontSize: 13, color: schedStatus?.running ? 'var(--success)' : 'var(--error)', fontWeight: 500 }}>
              Scheduler {schedStatus?.running ? 'running' : 'stopped'}
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
              · {schedStatus?.job_count ?? 0} active job{schedStatus?.job_count !== 1 ? 's' : ''}
            </span>
          </div>

          {/* Two-column lower section */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 20 }}>
            {/* Recent runs — real TaskRun records with status */}
            <div>
              <h2 style={{ fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: 16, margin: '0 0 12px', color: 'var(--text)' }}>
                Recent Runs
                <span style={{ fontSize: 12, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
                  {recentRuns.length} total
                </span>
              </h2>
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                {recentRuns.length === 0 ? (
                  <p style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: 13 }}>No runs yet.</p>
                ) : (
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        <th style={th}>Task</th>
                        <th style={th}>Triggered by</th>
                        <th style={th}>When</th>
                        <th style={th}>Result</th>
                        <th style={th} />
                      </tr>
                    </thead>
                    <tbody>
                      {recentRuns.slice(0, 12).map(run => {
                        const task = taskMap.get(run.task_id)
                        return (
                          <tr key={run.id} style={{ cursor: 'pointer' }} onClick={() => task && navigate(`/tasks/${task.id}`)}>
                            <td style={td}>
                              <div style={{ fontWeight: 500 }}>{task?.name ?? run.task_id.slice(0, 12) + '…'}</div>
                              {task && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}><TypeBadge type={task.type} /></div>}
                            </td>
                            <td style={{ ...td, fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                              {run.triggered_by}
                            </td>
                            <td style={{ ...td, fontSize: 12, color: 'var(--text-muted)' }}>{relTime(run.started_at)}</td>
                            <td style={td}><StatusBadge status={run.status} /></td>
                            <td style={td}><ArrowRight size={14} color="var(--text-muted)" /></td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            {/* Scheduled tasks */}
            <div>
              <h2 style={{ fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: 16, margin: '0 0 12px', color: 'var(--text)' }}>
                Upcoming Schedules
              </h2>
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                {scheduledJobs.length === 0 ? (
                  <p style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)', fontSize: 13 }}>No scheduled jobs.</p>
                ) : (
                  scheduledJobs
                    .sort((a, b) => (a.next_run_time ?? '').localeCompare(b.next_run_time ?? ''))
                    .map(job => (
                    <div
                      key={job.task_id}
                      style={{
                        padding: '12px 16px',
                        borderBottom: '1px solid var(--border)',
                        cursor: 'pointer',
                      }}
                      onClick={() => navigate(`/tasks/${job.task_id}`)}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontSize: 13, fontWeight: 500 }}>{job.task_name}</span>
                        <TypeBadge type={job.type} />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)' }}>
                        <span style={{ fontFamily: 'var(--font-mono)' }}>{job.trigger_description}</span>
                        <span>{fmtNext(job.next_run_time)}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Analytics charts */}
          {runsSummary && (
            <div style={{ marginTop: 24 }}>
              <h2 style={{ fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: 16, margin: '0 0 14px', color: 'var(--text)' }}>
                7-Day Run Activity
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {/* Success / failed stacked bar chart */}
                <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '16px 20px' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, fontWeight: 600 }}>
                    Runs per day
                  </div>
                  <ResponsiveContainer width="100%" height={120}>
                    <BarChart data={runsSummary.days.map((d, i) => ({
                      date: d.slice(5), // MM-DD
                      success: runsSummary.success[i],
                      failed: runsSummary.failed[i],
                    }))}>
                      <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                        labelStyle={{ color: 'var(--text)' }}
                        cursor={{ fill: 'var(--accent-dim)' }}
                      />
                      <Bar dataKey="success" fill="var(--success)" radius={[2, 2, 0, 0]} name="Success" stackId="a" />
                      <Bar dataKey="failed"  fill="var(--error)"   radius={[2, 2, 0, 0]} name="Failed"  stackId="a" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Per-task avg duration */}
                <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '16px 20px' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, fontWeight: 600 }}>
                    Avg duration per task (ms)
                  </div>
                  {!runsSummary.task_durations?.length ? (
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '32px 0', textAlign: 'center' }}>Not enough data yet.</p>
                  ) : (
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={runsSummary.task_durations.map(t => ({
                        name: t.task_name.length > 14 ? t.task_name.slice(0, 14) + '…' : t.task_name,
                        avg: t.avg_ms,
                      }))}>
                        <XAxis dataKey="name" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                        <Tooltip
                          contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                          formatter={(v) => [`${v}ms`, 'Avg']}
                          cursor={{ fill: 'var(--accent-dim)' }}
                        />
                        <Bar dataKey="avg" fill="var(--running)" radius={[2, 2, 0, 0]} name="Avg ms" />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>
    </div>
  )
}
