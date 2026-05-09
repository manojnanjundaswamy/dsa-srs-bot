import { useState } from 'react'
import { Plus, X } from 'lucide-react'

export default function ArgsEditor({ value, onChange }) {
  // value is a plain object like {"name":"Manoj","goal":"crack FAANG"}
  const [pairs, setPairs] = useState(() =>
    Object.entries(value ?? {}).map(([k, v]) => ({ key: k, val: String(v) }))
  )

  const commit = (updated) => {
    setPairs(updated)
    const obj = {}
    updated.forEach(({ key, val }) => { if (key.trim()) obj[key.trim()] = val })
    onChange(obj)
  }

  const add = () => commit([...pairs, { key: '', val: '' }])
  const remove = (i) => commit(pairs.filter((_, idx) => idx !== i))
  const update = (i, field, val) => {
    const next = pairs.map((p, idx) => idx === i ? { ...p, [field]: val } : p)
    commit(next)
  }

  const inp = {
    background: 'var(--surface-2)',
    border: '1px solid var(--border)',
    borderRadius: 6, color: 'var(--text)',
    padding: '7px 10px', fontSize: 12,
    fontFamily: 'var(--font-mono)',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      {pairs.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 6, alignItems: 'center',
          marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Key</span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Value</span>
          <span />
        </div>
      )}

      {pairs.map((p, i) => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 6, alignItems: 'center' }}>
          <input
            style={inp}
            placeholder="key"
            value={p.key}
            onChange={e => update(i, 'key', e.target.value)}
          />
          <input
            style={inp}
            placeholder="value"
            value={p.val}
            onChange={e => update(i, 'val', e.target.value)}
          />
          <button
            type="button"
            onClick={() => remove(i)}
            style={{
              width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'transparent', border: '1px solid var(--border)', borderRadius: 4,
              color: 'var(--text-muted)', cursor: 'pointer',
            }}
          >
            <X size={12} />
          </button>
        </div>
      ))}

      <button
        type="button"
        onClick={add}
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 10px', borderRadius: 6,
          border: '1px dashed var(--border)',
          background: 'transparent', color: 'var(--text-muted)',
          cursor: 'pointer', fontSize: 12, alignSelf: 'flex-start',
        }}
      >
        <Plus size={12} /> Add argument
      </button>
    </div>
  )
}
