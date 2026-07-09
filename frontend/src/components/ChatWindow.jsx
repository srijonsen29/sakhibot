import { useEffect, useRef }  from 'react'
import MessageBubble           from './MessageBubble'
import TypingIndicator         from './TypingIndicator'
import EmergencyBanner         from './EmergencyBanner'
import LocationPrompt          from './LocationPrompt'
import ScrollToBottom          from './ScrollToBottom'

export default function ChatWindow({
  messages, loading, history,
  askingLocation, onLocationSubmit,
}) {
  const containerRef = useRef(null)
  const bottomRef    = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const lastEmergency = [...messages]
    .reverse()
    .find(m => m.role === 'assistant' && m.isEmergency)

  return (
    <div className="flex-1 overflow-y-auto relative bg-white lg:bg-gray-50"
      ref={containerRef}>

      {lastEmergency && (
<div className="sticky top-0 z-10 pt-3 px-0 lg:px-4">
          <div className="max-w-3xl mx-auto">
            <EmergencyBanner severity={lastEmergency.severity} />
          </div>
        </div>
      )}
      {/* centered container for desktop */}
      <div className="max-w-3xl mx-auto py-4 space-y-4">

        {messages.length === 0 && <EmptyState />}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} history={history} />
        ))}

        {loading && <TypingIndicator />}

        {askingLocation && !loading && (
          <div className="px-4">
            <LocationPrompt onSubmit={onLocationSubmit} />
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <ScrollToBottom containerRef={containerRef} />
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center
                    min-h-64 px-8 text-center py-12">
      <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex
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
      <p className="text-sm font-semibold text-gray-700 mb-1">
        Ask anything about your rights
      </p>
      <p className="text-xs text-gray-400 leading-relaxed mb-5 max-w-sm">
        Domestic violence, workplace rights, maternity benefits,
        dowry laws — answered in your language, from real Indian law.
      </p>
      <div className="flex flex-wrap gap-2 justify-center">
        {[
          'What is domestic violence?',
          'How do I file an FIR?',
          'मुझे मदद चाहिए',
          'What is the POSH Act?',
        ].map((s, i) => (
          <span key={i}
            className="text-xs bg-emerald-50 text-emerald-700 border
                       border-emerald-200 rounded-full px-3 py-1.5
                       select-none">
            {s}
          </span>
        ))}
      </div>
    </div>
  )
}
