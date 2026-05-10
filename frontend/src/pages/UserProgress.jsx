import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, Flame, CheckCircle, Circle, Target } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'

const BASE = '/api'
async function req(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json()
}

const getUsers     = () => req(`${BASE}/users`)
const getAssets    = () => req(`${BASE}/assets`)
const getUserRecords = (uid, aid) => req(`${BASE}/users/${uid}/assets/${aid}/records?limit=200`)
const getUserStats   = (uid, aid) => req(`${BASE}/users/${uid}/assets/${aid}/stats`)
const getUserInteractions = (uid) => req(`${BASE}/users/${uid}/interactions?limit=30`)

const STATUS_DOT = {
  new:      { color: 'var(--text-muted)', label: 'New' },
  active:   { color: 'var(--running)',    label: 'Active' },
  mastered: { color: 'var(--success)',    label: 'Mastered' },
}

function StatCard({ label, value, sub, color }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '16px 20px' }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 28, color: color ?? 'var(--text)', lineHeight: 1 }}>{value ?? '—'}</div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{sub}</div>}
    </div>
  )
}

function relTime(iso) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60_000) return 'just now'
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)}h ago`
  return new Date(iso).toLocaleDateString()
}

export default function UserProgress() {
  const [selectedUser, setSelectedUser] = useState(null)
  const [selectedAsset, setSelectedAsset] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')

  const { data: users = [], isLoading: usersLoading } = useQuery({ queryKey: ['users'], queryFn: getUsers })
  const { data: assets = [] } = useQuery({ queryKey: ['assets'], queryFn: getAssets })

  // Auto-select first user and first asset
  const uid = selectedUser ?? users[0]?.id
  const aid = selectedAsset ?? assets[0]?.id

  const { data: records = [], isLoading: recLoading } = useQuery({
    queryKey: ['user-records', uid, aid],
    queryFn: () => getUserRecords(uid, aid),
    enabled: !!(uid && aid),
    refetchInterval: 30_000,
  })

  const { data: stats } = useQuery({
    queryKey: ['user-stats', uid, aid],
    queryFn: () => getUserStats(uid, aid),
    enabled: !!(uid && aid),
    refetchInterval: 30_000,
  })

  const { data: interactions = [] } = useQuery({
    queryKey: ['user-interactions', uid],
    queryFn: () => getUserInteractions(uid),
    enabled: !!uid,
    refetchInterval: 30_000,
  })

  const currentUser = users.find(u => u.id === uid)
  const currentAsset = assets.find(a => a.id === aid)

  const filtered = statusFilter === 'all'
    ? records
    : records.filter(r => r.state?.status === statusFilter)

  const th = { fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '8px 12px', textAlign: 'left', borderBottom: '1px solid var(--border)' }
  const td = { padding: '10px 12px', fontSize: 12, borderBottom: '1px solid var(--border)', verticalAlign: 'middle' }

  if (usersLoading) return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}>
      <Loader2 size={22} style={{ animation: 'spin 1s linear infinite' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 26, color: 'var(--text)' }}>
            {currentUser ? currentUser.name : 'Users'}
          </h1>
          {currentUser?.telegram_chat_id && (
            <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-muted)' }}>
              Telegram: {currentUser.telegram_chat_id}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {/* User selector */}
          {users.length > 1 && (
            <select value={uid ?? ''} onChange={e => setSelectedUser(e.target.value)}
              style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', padding: '7px 10px', fontSize: 13 }}>
              {users.map(u => <option key={u.id} value={u.id}>{u.name}</option>)}
            </select>
          )}
          {/* Asset selector */}
          <select value={aid ?? ''} onChange={e => setSelectedAsset(e.target.value)}
            style={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', padding: '7px 10px', fontSize: 13 }}>
            {assets.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
        </div>
      </div>

      {/* Stats cards */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 24 }}>
          <StatCard label="Total"    value={stats.total_records} />
          <StatCard label="Active"   value={stats.active_count}   color="var(--running)" />
          <StatCard label="Mastered" value={stats.mastered_count} color="var(--success)" />
          <StatCard label="Streak"   value={`${stats.streak_days}d`} color="var(--accent)"
            sub={stats.last_activity ? `Last: ${stats.last_activity}` : undefined} />
          <StatCard label="Solved"   value={stats.total_solved} color="var(--text)" />
        </div>
      )}

      {/* Weak patterns */}
      {stats?.weak_patterns?.length > 0 && (
        <div style={{
          background: 'rgba(224,84,84,0.08)', border: '1px solid rgba(224,84,84,0.25)',
          borderRadius: 8, padding: '12px 16px', marginBottom: 20,
        }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--error)', marginBottom: 6 }}>Patterns needing attention</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {stats.weak_patterns.map(wp => (
              <span key={wp.pattern} style={{
                background: 'rgba(224,84,84,0.15)', border: '1px solid rgba(224,84,84,0.3)',
                borderRadius: 4, padding: '2px 8px', fontSize: 12, color: 'var(--error)',
              }}>
                {wp.pattern} (avg ease {wp.avg_ease})
              </span>
            ))}
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20, alignItems: 'start' }}>
        {/* Progress table */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <h2 style={{ margin: 0, fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: 16, color: 'var(--text)' }}>
              {currentAsset?.name ?? 'Records'}
            </h2>
            <div style={{ display: 'flex', gap: 6, marginLeft: 'auto' }}>
              {['all', 'new', 'active', 'mastered'].map(s => (
                <button key={s} onClick={() => setStatusFilter(s)} style={{
                  padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 500,
                  border: `1px solid ${statusFilter === s ? 'var(--accent)' : 'var(--border)'}`,
                  background: statusFilter === s ? 'var(--accent-dim)' : 'transparent',
                  color: statusFilter === s ? 'var(--accent)' : 'var(--text-muted)',
                  cursor: 'pointer', textTransform: 'capitalize',
                }}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden', maxHeight: 520, overflowY: 'auto' }}>
            {recLoading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
                <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
              </div>
            ) : filtered.length === 0 ? (
              <p style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: 13 }}>No records.</p>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={th}>Record</th>
                    <th style={th}>Status</th>
                    <th style={th}>Ease</th>
                    <th style={th}>Interval</th>
                    <th style={th}>Reviews</th>
                    <th style={th}>Next due</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(rec => {
                    const s = rec.state ?? {}
                    const dot = STATUS_DOT[s.status] ?? STATUS_DOT.new
                    return (
                      <tr key={rec.record_key}>
                        <td style={td}>
                          <div style={{ fontWeight: 500 }}>{rec.data?.title ?? rec.record_key}</div>
                          {rec.data?.pattern && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{rec.data.pattern}</div>}
                        </td>
                        <td style={td}>
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12 }}>
                            <span style={{ width: 6, height: 6, borderRadius: '50%', background: dot.color, flexShrink: 0 }} />
                            {dot.label}
                          </span>
                        </td>
                        <td style={{ ...td, fontFamily: 'var(--font-mono)' }}>{s.ease_factor?.toFixed(1) ?? '—'}</td>
                        <td style={{ ...td, fontFamily: 'var(--font-mono)' }}>{s.interval_days ? `${s.interval_days}d` : '—'}</td>
                        <td style={{ ...td, fontFamily: 'var(--font-mono)' }}>{s.times_reviewed ?? 0}</td>
                        <td style={{ ...td, color: 'var(--text-muted)' }}>{s.next_due ?? '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Interaction log */}
        <div>
          <h2 style={{ margin: '0 0 12px', fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: 16, color: 'var(--text)' }}>
            Interaction Log
          </h2>
          <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
            {interactions.length === 0 ? (
              <p style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)', fontSize: 13 }}>No interactions yet.</p>
            ) : (
              interactions.map(i => (
                <div key={i.id} style={{ padding: '10px 14px', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                    <span style={{
                      fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em',
                      color: i.event_type === 'review' ? 'var(--success)' : i.event_type === 'error' ? 'var(--error)' : 'var(--running)',
                    }}>
                      {i.event_type}
                    </span>
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{relTime(i.created_at)}</span>
                  </div>
                  {i.record_key && <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>{i.record_key}</div>}
                  {i.event_data && Object.keys(i.event_data).length > 0 && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {JSON.stringify(i.event_data).slice(0, 60)}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
