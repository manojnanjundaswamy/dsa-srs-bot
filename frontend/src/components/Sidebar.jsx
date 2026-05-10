import { NavLink } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { LayoutDashboard, LayoutList, Plus, Zap, Database, Users } from 'lucide-react'
import { getSchedulerStatus } from '../api/client'

const NAV = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/tasks',     icon: LayoutList,      label: 'Tasks' },
  { to: '/tasks/new', icon: Plus,            label: 'New Task' },
  { to: '/assets',    icon: Database,        label: 'Assets' },
  { to: '/users',     icon: Users,           label: 'Users' },
]

export default function Sidebar() {
  const { data } = useQuery({
    queryKey: ['scheduler-status'],
    queryFn: getSchedulerStatus,
    refetchInterval: 15_000,
  })

  const running = data?.running ?? false

  return (
    <aside style={{
      width: 220, flexShrink: 0,
      background: 'var(--surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column',
      height: '100%',
    }}>
      {/* Logo */}
      <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Zap size={18} color="var(--accent)" fill="var(--accent)" />
          <span style={{ fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 16, color: 'var(--text)' }}>
            Task Engine
          </span>
        </div>
        {/* Scheduler pill */}
        <div style={{
          marginTop: 10,
          display: 'inline-flex', alignItems: 'center', gap: 6,
          background: running ? 'rgba(78, 201, 148, 0.12)' : 'rgba(224, 84, 84, 0.1)',
          border: `1px solid ${running ? 'rgba(78,201,148,0.3)' : 'rgba(224,84,84,0.3)'}`,
          borderRadius: 20, padding: '3px 10px',
          fontSize: 11, color: running ? 'var(--success)' : 'var(--error)',
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%',
            background: running ? 'var(--success)' : 'var(--error)',
            animation: running ? 'pulse 2s infinite' : 'none',
          }} />
          {running ? `Scheduler · ${data?.job_count ?? 0} jobs` : 'Scheduler stopped'}
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '12px 10px' }}>
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 10px', borderRadius: 6,
              textDecoration: 'none', marginBottom: 2,
              fontSize: 13, fontWeight: isActive ? 500 : 400,
              color: isActive ? 'var(--accent)' : 'var(--text-muted)',
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              transition: 'all 0.15s',
            })}
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '12px 20px',
        borderTop: '1px solid var(--border)',
        fontSize: 11, color: 'var(--text-muted)',
      }}>
        API · <a href="http://localhost:8080/docs" target="_blank" rel="noreferrer"
          style={{ color: 'var(--accent)', textDecoration: 'none' }}>localhost:8080/docs</a>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </aside>
  )
}
