import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Sparkles, PenLine, ChevronLeft, Save } from 'lucide-react'
import PromptGenerator from '../components/PromptGenerator'
import ScriptEditor from '../components/ScriptEditor'
import TriggerBuilder from '../components/TriggerBuilder'
import ArgsEditor from '../components/ArgsEditor'
import { createTask, updateTask, getTask } from '../api/client'
import { useToast } from '../components/Toast'

const DEFAULT_SCRIPT = '# Write your Python script here\n# All bot functions are available: morning_mode(), send_telegram_message(), etc.\n\nprint("Task running!")\n'

const SECTION = ({ title, children }) => (
  <div style={{
    background: 'var(--surface)', border: '1px solid var(--border)',
    borderRadius: 8, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12,
  }}>
    <h3 style={{ margin: 0, fontFamily: 'var(--font-head)', fontWeight: 600, fontSize: 14, color: 'var(--text)' }}>
      {title}
    </h3>
    {children}
  </div>
)

const Label = ({ children }) => (
  <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
    {children}
  </label>
)

const Input = (props) => (
  <input {...props} style={{
    background: 'var(--surface-2)', border: '1px solid var(--border)',
    borderRadius: 6, color: 'var(--text)', padding: '9px 12px',
    fontSize: 13, fontFamily: 'var(--font-ui)', width: '100%',
    ...props.style,
  }} />
)

const TextArea = (props) => (
  <textarea {...props} style={{
    background: 'var(--surface-2)', border: '1px solid var(--border)',
    borderRadius: 6, color: 'var(--text)', padding: '9px 12px',
    fontSize: 13, fontFamily: 'var(--font-ui)', resize: 'vertical',
    lineHeight: 1.5, width: '100%',
    ...props.style,
  }} />
)

export default function TaskBuilder() {
  const { id } = useParams()
  const isEdit = !!id
  const navigate = useNavigate()
  const qc = useQueryClient()
  const toast = useToast()

  // Form state
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [mode, setMode] = useState('ai') // 'ai' | 'manual'
  const [script, setScript] = useState(DEFAULT_SCRIPT)
  const [prompt, setPrompt] = useState('')
  const [type, setType] = useState('manual')
  const [trigConfig, setTrigConfig] = useState({})
  const [args, setArgs] = useState({})
  const [enabled, setEnabled] = useState(true)
  const [error, setError] = useState(null)

  // Load existing task for edit mode
  const { data: existing } = useQuery({
    queryKey: ['task', id],
    queryFn: () => getTask(id),
    enabled: isEdit,
  })

  useEffect(() => {
    if (existing) {
      setName(existing.name)
      setDesc(existing.description ?? '')
      setScript(existing.script)
      setPrompt(existing.prompt ?? '')
      setType(existing.type)
      setTrigConfig(existing.trigger_config ?? {})
      setArgs(existing.script_args ?? {})
      setEnabled(existing.enabled)
      setMode(existing.prompt ? 'ai' : 'manual')
    }
  }, [existing])

  const saveMut = useMutation({
    mutationFn: (body) => isEdit ? updateTask(id, body) : createTask(body),
    onSuccess: (task) => {
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['scheduler-status'] })
      toast(isEdit ? `"${task.name}" saved` : `"${task.name}" created`, 'success')
      navigate(`/tasks/${task.id}`)
    },
    onError: (e) => { setError(e.message); toast(e.message, 'error') },
  })

  const handleGenerated = (result) => {
    setScript(result.script)
    if (!name) setName(result.suggested_name)
    if (result.suggested_type) setType(result.suggested_type)
    if (Object.keys(result.suggested_trigger ?? {}).length) setTrigConfig(result.suggested_trigger)
    setMode('manual') // show editor after generation
  }

  const save = () => {
    if (!name.trim()) { setError('Task name is required'); return }
    if (!script.trim()) { setError('Script is required'); return }
    setError(null)
    saveMut.mutate({ name, description: desc, type, trigger_config: trigConfig, script, script_args: args, prompt, enabled })
  }

  const modeBtn = (m, icon, label) => (
    <button
      type="button"
      onClick={() => setMode(m)}
      style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        padding: '10px 0', borderRadius: 6,
        border: `1px solid ${mode === m ? 'var(--accent)' : 'var(--border)'}`,
        background: mode === m ? 'var(--accent-dim)' : 'var(--surface-2)',
        color: mode === m ? 'var(--accent)' : 'var(--text-muted)',
        cursor: 'pointer', fontWeight: 500, fontSize: 13,
      }}
    >
      {icon} {label}
    </button>
  )

  return (
    <div style={{ maxWidth: 760 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
        <button onClick={() => navigate(-1)} style={{
          display: 'flex', alignItems: 'center', gap: 4,
          background: 'transparent', border: '1px solid var(--border)',
          borderRadius: 6, padding: '6px 10px',
          color: 'var(--text-muted)', cursor: 'pointer', fontSize: 12,
        }}>
          <ChevronLeft size={14} /> Back
        </button>
        <h1 style={{
          margin: 0, fontFamily: 'var(--font-head)', fontWeight: 700,
          fontSize: 24, color: 'var(--text)',
        }}>
          {isEdit ? 'Edit Task' : 'New Task'}
        </h1>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Task info */}
        <SECTION title="Task Info">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Label>Name *</Label>
            <Input placeholder="e.g. Weekly Stats Summary" value={name} onChange={e => setName(e.target.value)} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Label>Description</Label>
            <TextArea rows={2} placeholder="What does this task do?" value={desc} onChange={e => setDesc(e.target.value)} />
          </div>
        </SECTION>

        {/* Script source */}
        <SECTION title="Script">
          <div style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
            {modeBtn('ai', <Sparkles size={14} />, 'Generate with AI')}
            {modeBtn('manual', <PenLine size={14} />, 'Write manually')}
          </div>

          {mode === 'ai' && (
            <>
              <PromptGenerator onGenerated={handleGenerated} />
              {script !== DEFAULT_SCRIPT && (
                <div style={{ marginTop: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                    <Label>Generated script</Label>
                    <button type="button" onClick={() => setMode('manual')}
                      style={{ fontSize: 11, color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                      Edit manually →
                    </button>
                  </div>
                  <ScriptEditor value={script} readOnly minHeight={160} />
                </div>
              )}
            </>
          )}

          {mode === 'manual' && (
            <ScriptEditor value={script} onChange={setScript} minHeight={220} />
          )}

          <p style={{ margin: 0, fontSize: 11, color: 'var(--text-muted)' }}>
            Available: <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>morning_mode()</code>, <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>send_telegram_message()</code>, <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>load_tracker()</code>, and all bot functions.
          </p>
        </SECTION>

        {/* Trigger */}
        <SECTION title="Trigger">
          <TriggerBuilder
            type={type}
            config={trigConfig}
            onChange={setTrigConfig}
            onTypeChange={setType}
          />
        </SECTION>

        {/* Args */}
        <SECTION title="Script Arguments (optional)">
          <p style={{ margin: 0, fontSize: 12, color: 'var(--text-muted)' }}>
            These are available as <code style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>args['key']</code> inside your script.
          </p>
          <ArgsEditor value={args} onChange={setArgs} />
        </SECTION>

        {/* Settings */}
        <SECTION title="Settings">
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
            <div
              onClick={() => setEnabled(e => !e)}
              style={{
                width: 36, height: 20, borderRadius: 10,
                background: enabled ? 'var(--accent)' : 'var(--surface-2)',
                border: `1px solid ${enabled ? 'var(--accent)' : 'var(--border)'}`,
                position: 'relative', cursor: 'pointer', transition: 'all 0.2s',
              }}
            >
              <div style={{
                width: 14, height: 14, borderRadius: '50%', background: '#fff',
                position: 'absolute', top: 2, left: enabled ? 18 : 2,
                transition: 'left 0.2s',
              }} />
            </div>
            <span style={{ fontSize: 13 }}>Enabled</span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {enabled ? 'Task will run on schedule' : 'Task is disabled'}
            </span>
          </label>
        </SECTION>

        {/* Error + actions */}
        {error && (
          <p style={{ color: 'var(--error)', fontSize: 13, margin: 0 }}>{error}</p>
        )}

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', paddingBottom: 40 }}>
          <button onClick={() => navigate(-1)} style={{
            padding: '10px 20px', borderRadius: 6, border: '1px solid var(--border)',
            background: 'transparent', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 13,
          }}>
            Cancel
          </button>
          <button
            onClick={save}
            disabled={saveMut.isPending}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '10px 22px', borderRadius: 6,
              background: 'var(--accent)', border: 'none',
              color: '#111', fontWeight: 600, fontSize: 13, cursor: 'pointer',
              opacity: saveMut.isPending ? 0.6 : 1,
            }}
          >
            <Save size={14} />
            {saveMut.isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Save & Activate'}
          </button>
        </div>
      </div>
    </div>
  )
}
