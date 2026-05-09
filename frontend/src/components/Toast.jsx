import { useState, useCallback, createContext, useContext } from 'react'
import { CheckCircle2, XCircle, Info, X } from 'lucide-react'

const ToastContext = createContext(null)

const ICONS = {
  success: <CheckCircle2 size={16} color="var(--success)" />,
  error:   <XCircle size={16} color="var(--error)" />,
  info:    <Info size={16} color="var(--running)" />,
}

let _nextId = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const show = useCallback((message, type = 'info', duration = 3500) => {
    const id = ++_nextId
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration)
  }, [])

  const dismiss = useCallback((id) => setToasts(prev => prev.filter(t => t.id !== id)), [])

  return (
    <ToastContext.Provider value={show}>
      {children}
      {/* Toast container */}
      <div style={{
        position: 'fixed', bottom: 24, right: 24,
        display: 'flex', flexDirection: 'column', gap: 8,
        zIndex: 9999, pointerEvents: 'none',
      }}>
        {toasts.map(t => (
          <div
            key={t.id}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 8, padding: '10px 14px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
              animation: 'slideIn 0.2s ease',
              pointerEvents: 'all',
              minWidth: 240, maxWidth: 360,
            }}
          >
            {ICONS[t.type] ?? ICONS.info}
            <span style={{ flex: 1, fontSize: 13, color: 'var(--text)', lineHeight: 1.4 }}>
              {t.message}
            </span>
            <button
              onClick={() => dismiss(t.id)}
              style={{
                background: 'none', border: 'none',
                color: 'var(--text-muted)', cursor: 'pointer',
                padding: 0, display: 'flex', alignItems: 'center',
              }}
            >
              <X size={13} />
            </button>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(20px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used inside ToastProvider')
  return ctx
}
