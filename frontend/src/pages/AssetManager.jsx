import { useState, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Database, Upload, Pencil, Check, X, Plus } from 'lucide-react'
import { getTasks } from '../api/client'
import { useToast } from '../components/Toast'

const BASE = '/api'
const H = { 'Content-Type': 'application/json' }

async function req(url, opts = {}) {
  const res = await fetch(url, opts)
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`)
  if (res.status === 204) return null
  return res.json()
}

const getAssets   = () => req(`${BASE}/assets`)
const getRecords  = (id) => req(`${BASE}/assets/${id}/records?limit=200`)
const linkTask    = (tid, aid, role) => req(`${BASE}/tasks/${tid}/assets`, { method: 'POST', headers: H, body: JSON.stringify({ asset_id: aid, role }) })
const updateAsset = (id, body) => req(`${BASE}/assets/${id}`, { method: 'PUT', headers: H, body: JSON.stringify(body) })
const updateRecord = (assetId, key, body) => req(`${BASE}/assets/${assetId}/records/${key}`, { method: 'PUT', headers: H, body: JSON.stringify(body) })
const createRecord = (assetId, body) => req(`${BASE}/assets/${assetId}/records`, { method: 'POST', headers: H, body: JSON.stringify(body) })

const inp = (extra = {}) => ({
  background: 'var(--surface-2)', border: '1px solid var(--border)',
  borderRadius: 6, color: 'var(--text)', padding: '7px 10px', fontSize: 13,
  fontFamily: 'var(--font-ui)', width: '100%', ...extra,
})

// Inline cell editor
function EditableCell({ value, onSave }) {
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(value ?? '')

  if (!editing) {
    return (
      <span
        onDoubleClick={() => setEditing(true)}
        title="Double-click to edit"
        style={{ cursor: 'text', display: 'block', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
      >
        {value ?? <span style={{ color: 'var(--text-muted)' }}>—</span>}
      </span>
    )
  }

  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
      <input
        autoFocus
        value={val}
        onChange={e => setVal(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter') { onSave(val); setEditing(false) }
          if (e.key === 'Escape') setEditing(false)
        }}
        style={{ ...inp(), padding: '4px 8px', fontSize: 12, width: 120 }}
      />
      <button onClick={() => { onSave(val); setEditing(false) }}
        style={{ background: 'none', border: 'none', color: 'var(--success)', cursor: 'pointer', padding: 2 }}>
        <Check size={13} />
      </button>
      <button onClick={() => setEditing(false)}
        style={{ background: 'none', border: 'none', color: 'var(--error)', cursor: 'pointer', padding: 2 }}>
        <X size={13} />
      </button>
    </div>
  )
}

// Asset metadata edit form
function AssetEditPanel({ asset, onSave, onCancel }) {
  const [name, setName] = useState(asset.name)
  const [desc, setDesc] = useState(asset.description ?? '')
  const [type, setType] = useState(asset.type ?? 'generic')
  const toast = useToast()

  const save = async () => {
    try {
      await onSave({ name, description: desc, type })
      toast('Asset updated', 'success')
    } catch (e) { toast(e.message, 'error') }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '16px 0' }}>
      <div>
        <label style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>Name</label>
        <input style={inp()} value={name} onChange={e => setName(e.target.value)} />
      </div>
      <div>
        <label style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>Type</label>
        <input style={inp()} value={type} onChange={e => setType(e.target.value)} />
      </div>
      <div>
        <label style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>Description</label>
        <textarea rows={2} style={{ ...inp(), resize: 'vertical' }} value={desc} onChange={e => setDesc(e.target.value)} />
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={save} style={{ padding: '7px 16px', borderRadius: 6, background: 'var(--accent)', border: 'none', color: '#111', fontWeight: 600, fontSize: 12, cursor: 'pointer' }}>Save</button>
        <button onClick={onCancel} style={{ padding: '7px 16px', borderRadius: 6, background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer' }}>Cancel</button>
      </div>
    </div>
  )
}

export default function AssetManager() {
  const qc = useQueryClient()
  const toast = useToast()
  const fileRef = useRef(null)
  const [selectedId, setSelectedId] = useState(null)
  const [editingAsset, setEditingAsset] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [newRecordJson, setNewRecordJson] = useState('')
  const [showAddRecord, setShowAddRecord] = useState(false)

  const { data: assets = [], isLoading } = useQuery({ queryKey: ['assets'], queryFn: getAssets, refetchInterval: 30_000 })
  const { data: records = [], isLoading: recLoading, refetch: refetchRecords } = useQuery({
    queryKey: ['asset-records', selectedId],
    queryFn: () => getRecords(selectedId),
    enabled: !!selectedId,
  })
  const { data: tasks = [] } = useQuery({ queryKey: ['tasks'], queryFn: getTasks })

  const selected = assets.find(a => a.id === selectedId)

  const refreshAll = () => {
    qc.invalidateQueries({ queryKey: ['assets'] })
    qc.invalidateQueries({ queryKey: ['asset-records', selectedId] })
  }

  // Save asset metadata
  const handleSaveAsset = async (body) => {
    await updateAsset(selectedId, body)
    refreshAll()
    setEditingAsset(false)
  }

  // Inline record field edit
  const handleEditRecordField = async (record, field, newValue) => {
    const updated = { ...record.data, [field]: newValue }
    try {
      await updateRecord(selectedId, record.record_key, { data: updated })
      refetchRecords()
      toast('Record updated', 'success')
    } catch (e) { toast(e.message, 'error') }
  }

  // File upload — JSON array or JSONL
  const handleFileUpload = async (file) => {
    setUploading(true)
    try {
      const text = await file.text()
      let items = []
      if (file.name.endsWith('.json')) {
        const parsed = JSON.parse(text)
        items = Array.isArray(parsed) ? parsed : [parsed]
      } else {
        // JSONL or TXT — one JSON object per line
        items = text.split('\n').filter(l => l.trim()).map(l => JSON.parse(l.trim()))
      }

      let added = 0
      let skipped = 0
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        const key = item.id ?? item.key ?? item.record_key ?? `record-${i}`
        try {
          await createRecord(selectedId, { record_key: key, data: item, order: i })
          added++
        } catch (_) {
          skipped++
        }
      }
      refetchRecords()
      toast(`Imported ${added} records${skipped > 0 ? ` (${skipped} skipped — already exist)` : ''}`, 'success')
    } catch (e) {
      toast(`Upload failed: ${e.message}`, 'error')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  // Add a single new record
  const handleAddRecord = async () => {
    try {
      const body = JSON.parse(newRecordJson)
      const key = body.id ?? body.key ?? `record-${Date.now()}`
      await createRecord(selectedId, { record_key: key, data: body, order: records.length })
      refetchRecords()
      setNewRecordJson('')
      setShowAddRecord(false)
      toast('Record added', 'success')
    } catch (e) { toast(`Invalid JSON or duplicate key: ${e.message}`, 'error') }
  }

  const th = { fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', padding: '8px 12px', textAlign: 'left', borderBottom: '1px solid var(--border)' }
  const td = { padding: '8px 12px', fontSize: 12, borderBottom: '1px solid var(--border)', verticalAlign: 'middle' }

  // Derive data columns from first record
  const dataCols = records.length > 0 ? Object.keys(records[0].data ?? {}).slice(0, 5) : []

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 26, color: 'var(--text)' }}>Assets</h1>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--text-muted)' }}>Datasets and records used by tasks</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20, alignItems: 'start' }}>
        {/* Left: asset list */}
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Database size={14} color="var(--accent)" />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Datasets</span>
            <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>{assets.length}</span>
          </div>
          {isLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 24 }}>
              <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
            </div>
          ) : assets.map(asset => (
            <div
              key={asset.id}
              onClick={() => { setSelectedId(asset.id); setEditingAsset(false) }}
              style={{
                padding: '12px 16px', cursor: 'pointer',
                background: selectedId === asset.id ? 'var(--accent-dim)' : 'transparent',
                borderLeft: `3px solid ${selectedId === asset.id ? 'var(--accent)' : 'transparent'}`,
                borderBottom: '1px solid var(--border)', transition: 'all 0.15s',
              }}
            >
              <div style={{ fontWeight: 500, fontSize: 13 }}>{asset.name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{asset.type}</div>
              {asset.description && (
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  {asset.description.slice(0, 48)}{asset.description.length > 48 ? '…' : ''}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Right: records panel */}
        <div>
          {!selected ? (
            <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '48px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
              Select a dataset to browse its records.
            </div>
          ) : (
            <>
              {/* Asset header */}
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '16px 20px', marginBottom: 16 }}>
                {editingAsset ? (
                  <AssetEditPanel asset={selected} onSave={handleSaveAsset} onCancel={() => setEditingAsset(false)} />
                ) : (
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                    <div style={{ flex: 1 }}>
                      <h2 style={{ margin: 0, fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: 18, color: 'var(--text)' }}>{selected.name}</h2>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{selected.type} · {records.length} records</span>
                      {selected.description && <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--text-muted)' }}>{selected.description}</p>}
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexShrink: 0, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                      {/* Edit asset metadata */}
                      <button onClick={() => setEditingAsset(true)} style={{
                        display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px',
                        borderRadius: 6, background: 'var(--surface-2)', border: '1px solid var(--border)',
                        color: 'var(--text-muted)', cursor: 'pointer', fontSize: 12,
                      }}>
                        <Pencil size={12} /> Edit Info
                      </button>

                      {/* File upload */}
                      <label style={{
                        display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px',
                        borderRadius: 6, background: uploading ? 'var(--surface-2)' : 'var(--accent-dim)',
                        border: '1px solid rgba(232,160,48,0.3)', color: 'var(--accent)',
                        cursor: 'pointer', fontSize: 12, fontWeight: 500,
                      }}>
                        {uploading ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Upload size={12} />}
                        {uploading ? 'Importing…' : 'Upload JSON/TXT'}
                        <input
                          ref={fileRef}
                          type="file"
                          accept=".json,.txt,.jsonl"
                          style={{ display: 'none' }}
                          onChange={e => { if (e.target.files[0]) handleFileUpload(e.target.files[0]) }}
                        />
                      </label>

                      {/* Add single record */}
                      <button onClick={() => setShowAddRecord(v => !v)} style={{
                        display: 'flex', alignItems: 'center', gap: 5, padding: '6px 12px',
                        borderRadius: 6, background: 'var(--surface-2)', border: '1px solid var(--border)',
                        color: 'var(--text-muted)', cursor: 'pointer', fontSize: 12,
                      }}>
                        <Plus size={12} /> Add Record
                      </button>

                      {/* Link to task */}
                      <select defaultValue="" onChange={e => {
                        if (!e.target.value) return
                        linkTask(e.target.value, selected.id, 'read')
                          .then(() => { toast('Linked to task', 'success'); e.target.value = '' })
                          .catch(err => toast(err.message, 'error'))
                      }} style={{ ...inp({ width: 'auto', padding: '6px 10px', fontSize: 12 }) }}>
                        <option value="">Link to task…</option>
                        {tasks.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                      </select>
                    </div>
                  </div>
                )}

                {/* Add single record panel */}
                {showAddRecord && !editingAsset && (
                  <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '0 0 8px' }}>
                      Paste a JSON object for the new record. Include an <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>id</code> or <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>key</code> field to use as the record key.
                    </p>
                    <textarea
                      rows={4}
                      placeholder={'{"id":"my-key","title":"My Item","difficulty":"Easy"}'}
                      value={newRecordJson}
                      onChange={e => setNewRecordJson(e.target.value)}
                      style={{ ...inp({ fontFamily: 'var(--font-mono)', fontSize: 12, resize: 'vertical' }) }}
                    />
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                      <button onClick={handleAddRecord} style={{
                        padding: '6px 14px', borderRadius: 6, background: 'var(--accent)', border: 'none',
                        color: '#111', fontWeight: 600, fontSize: 12, cursor: 'pointer',
                      }}>Add</button>
                      <button onClick={() => { setShowAddRecord(false); setNewRecordJson('') }} style={{
                        padding: '6px 14px', borderRadius: 6, background: 'transparent',
                        border: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer',
                      }}>Cancel</button>
                    </div>
                  </div>
                )}
              </div>

              {/* Upload format hint */}
              <div style={{ marginBottom: 12, fontSize: 11, color: 'var(--text-muted)' }}>
                Upload accepts: JSON array <code style={{ fontFamily: 'var(--font-mono)', background: 'var(--surface-2)', padding: '1px 5px', borderRadius: 3 }}>[{"{"}&quot;id&quot;:…{"}"}, …]</code> or one JSON object per line (JSONL). Double-click any cell to edit it inline.
              </div>

              {/* Records table */}
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
                {recLoading ? (
                  <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
                    <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                  </div>
                ) : records.length === 0 ? (
                  <p style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-muted)', fontSize: 13 }}>
                    No records yet. Upload a JSON file or add a record above.
                  </p>
                ) : (
                  <>
                    <div style={{ overflowX: 'auto', maxHeight: 520, overflowY: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 600 }}>
                        <thead style={{ position: 'sticky', top: 0, background: 'var(--surface)', zIndex: 1 }}>
                          <tr>
                            <th style={th}>#</th>
                            <th style={th}>Key</th>
                            {dataCols.map(k => <th key={k} style={th}>{k}</th>)}
                          </tr>
                        </thead>
                        <tbody>
                          {records.map((rec) => (
                            <tr key={rec.record_key}>
                              <td style={{ ...td, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>{rec.order + 1}</td>
                              <td style={{ ...td, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent)' }}>{rec.record_key}</td>
                              {dataCols.map(k => (
                                <td key={k} style={{ ...td, maxWidth: 160 }}>
                                  <EditableCell
                                    value={String(rec.data[k] ?? '')}
                                    onSave={val => handleEditRecordField(rec, k, val)}
                                  />
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div style={{ padding: '8px 14px', fontSize: 11, color: 'var(--text-muted)', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between' }}>
                      <span>{records.length} records</span>
                      <span style={{ fontFamily: 'var(--font-mono)' }}>{selected.id}</span>
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
