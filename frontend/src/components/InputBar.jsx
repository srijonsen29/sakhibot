import { useState, useRef } from 'react'
import VoiceButton from './VoiceButton'

export default function InputBar({ onSend, loading, lang = 'en' }) {
  const [text, setText] = useState('')
  const inputRef = useRef(null)

  const submit = () => {
    const trimmed = text.trim()
    if (!trimmed || loading) return
    onSend(trimmed)
    setText('')
    inputRef.current?.focus()
  }

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-gray-100 bg-white px-4 py-3 sm:px-6">
      <div className="mx-auto flex w-full max-w-3xl items-end gap-2">
        <VoiceButton
          lang={lang}
          onResult={t => setText(t)}
          disabled={loading}
        />

        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Type or speak your question..."
            rows={1}
            style={{ resize: 'none' }}
            className="w-full bg-gray-50 border border-gray-200 rounded-2xl
                       px-4 py-2.5 text-sm text-gray-800 placeholder-gray-400
                       focus:outline-none focus:ring-2 focus:ring-emerald-300
                       focus:border-emerald-400 transition-colors leading-relaxed
                       max-h-32 overflow-y-auto"
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
            }}
            disabled={loading}
          />
        </div>

        <button
          onClick={submit}
          disabled={!text.trim() || loading}
          className="w-10 h-10 bg-emerald-600 hover:bg-emerald-700
                     disabled:bg-gray-200 text-white rounded-full flex
                     items-center justify-center transition-colors shrink-0"
          title="Send message"
        >
          {loading
            ? <svg className="w-4 h-4 animate-spin" fill="none"
                viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10"
                  stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
            : <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24"
                stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round"
                  strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
              </svg>
          }
        </button>
      </div>
    </div>
  )
}
