import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'

export default function ScriptEditor({ value, onChange, readOnly = false, minHeight = 200 }) {
  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 6, overflow: 'hidden',
    }}>
      <CodeMirror
        value={value}
        height={`${minHeight}px`}
        theme={oneDark}
        extensions={[python()]}
        editable={!readOnly}
        onChange={onChange}
        basicSetup={{
          lineNumbers: true,
          foldGutter: false,
          dropCursor: false,
          allowMultipleSelections: false,
          indentOnInput: true,
          autocompletion: !readOnly,
        }}
      />
    </div>
  )
}
