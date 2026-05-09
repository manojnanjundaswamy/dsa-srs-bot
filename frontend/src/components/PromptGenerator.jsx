import { useState } from 'react'
import { Sparkles, Loader2 } from 'lucide-react'
import { generateScript } from '../api/client'

export default function PromptGenerator({ onGenerated }) {
  const [prompt, setPrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const generate = async () => {
    if (!prompt.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await generateScript({ prompt, context_hint: 'Telegram DSA study bot' })
      onGenerated(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <textarea
        rows={4}
        placeholder="Describe what this task should do...&#10;e.g. Every Monday at 9 AM, send my learning stats and weak areas to Telegram"
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        style={{
          background: 'var(--surface-2)',
          border: '1px solid var(--border)',
          borderRadius: 6, color: 'var(--text)',
          padding: '10px 12px', fontSize: 13,
          fontFamily: 'var(--font-ui)', resize: 'vertical',
          lineHeight: 1.5,
        }}
      />
      {error && (
        <p style={{ color: 'var(--error)', fontSize: 12, margin: 0 }}>{error}</p>
      )}
      <button
        type="button"
        onClick={generate}
        disabled={!prompt.trim() || loading}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '10px 18px', borderRadius: 6,
          background: loading || !prompt.trim() ? 'var(--surface-2)' : 'var(--accent)',
          border: 'none', color: loading || !prompt.trim() ? 'var(--text-muted)' : '#111',
          cursor: loading || !prompt.trim() ? 'not-allowed' : 'pointer',
          fontWeight: 600, fontSize: 13, alignSelf: 'flex-start',
        }}
      >
        {loading
          ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Generating…</>
          : <><Sparkles size={14} /> Generate Script</>
        }
      </button>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
