import { useEffect, useRef } from 'react'
import MessageBubble    from './MessageBubble'
import TypingIndicator  from './TypingIndicator'
import EmergencyBanner  from './EmergencyBanner'

export default function ChatWindow({ messages, loading, history }) {
  const bottomRef = useRef(null)

  // auto-scroll to bottom on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const lastEmergency = messages.findLast?.(m => m.isEmergency) || null

  return (
    <div className="flex-1 overflow-y-auto py-4 sm:py-6 space-y-4">

      {/* emergency banner — shown if last bot message was emergency */}
      {lastEmergency && (
        <EmergencyBanner helplines={lastEmergency.helplines} />
      )}

      {/* empty state */}
      {messages.length === 0 && (
        <div className="mx-auto flex h-full min-h-64 max-w-2xl flex-col
                        items-center justify-center px-6 text-center sm:px-8">
          <div className="w-14 h-14 bg-emerald-100 rounded-full flex
                          items-center justify-center mb-4">
            <svg className="w-7 h-7 text-emerald-600" fill="none"
              viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03
                   8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72
                   C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9
                   3.582 9 8z" />
            </svg>
          </div>
          <p className="text-sm font-medium text-gray-700 mb-1">
            Ask me anything about your rights
          </p>
          <p className="max-w-md text-xs text-gray-400 leading-relaxed
                        sm:text-sm">
            I can help with domestic violence, workplace rights,
            maternity benefits, dowry laws, and more — in your language.
          </p>
          <div className="flex flex-wrap gap-2 mt-5 justify-center">
            {STARTER_PROMPTS.map((p, i) => (
              <StarterChip key={i} text={p} />
            ))}
          </div>
        </div>
      )}

      {/* messages */}
      {messages.map((msg, i) => (
        <MessageBubble key={i} msg={msg} history={history} />
      ))}

      {/* typing indicator */}
      {loading && <TypingIndicator />}

      <div ref={bottomRef} />
    </div>
  )
}

const STARTER_PROMPTS = [
  'What is domestic violence?',
  'How do I file an FIR?',
  'What is the POSH Act?',
  'मुझे मदद चाहिए',
]

function StarterChip({ text }) {
  return (
    <span className="text-xs bg-emerald-50 text-emerald-700 border
                     border-emerald-200 rounded-full px-3 py-1.5 cursor-default
                     select-none">
      {text}
    </span>
  )
}
