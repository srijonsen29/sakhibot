
import { useState } from 'react'
import SourceCard     from './SourceCard'
import ResourceCard   from './ResourceCard'
import SafetyPlanCard from './SafetyPlanCard'
import DocumentCard   from './DocumentCard'

export default function MessageBubble({ msg, history }) {
  const isUser = msg.role === 'user'

  if (isUser) {
    return (
      <div className="mx-auto flex w-full max-w-3xl justify-end px-4 sm:px-6">
        <div className="max-w-[86%] sm:max-w-[72%] bg-emerald-600 text-white rounded-2xl
                        rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed
                        shadow-sm">
          {msg.content}
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl items-start gap-2.5
                    px-4 sm:px-6">
      {/* avatar */}
      <div className="w-7 h-7 rounded-full bg-emerald-100 flex items-center
                      justify-center text-emerald-700 text-xs font-bold
                      shrink-0 mt-0.5 select-none">
        S
      </div>

      <div className="flex-1 min-w-0 max-w-[92%] sm:max-w-[82%]">
        {/* main bubble */}
        <div className={`rounded-2xl rounded-tl-sm px-4 py-3 text-sm
                        leading-relaxed shadow-sm
                        ${msg.isEmergency
                          ? 'bg-red-50 border border-red-200 text-red-900'
                          : 'bg-gray-100 text-gray-800'
                        }`}>
          <MessageText text={msg.content} />
        </div>

        {/* source citations */}
        {msg.sources?.length > 0 && (
          <SourceCard sources={msg.sources} />
        )}

        {/* document download card */}
        {msg.documentReady && msg.documentType && (
          <DocumentCard
            documentType={msg.documentType}
            history={history}
          />
        )}

        {/* resource + helpline cards */}
        {(msg.resources?.length > 0 || msg.helplines?.length > 0) && (
          <ResourceCard
            resources={msg.resources}
            helplines={msg.helplines}
          />
        )}

        {/* safety plan */}
        {msg.safetyPlan?.length > 0 && (
          <SafetyPlanCard steps={msg.safetyPlan} />
        )}

        {/* bottom actions */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 mt-2 px-1">
          {/* TTS button */}
          <TTSButton text={msg.content} lang={msg.detectedLang} />

          {/* WhatsApp share */}
          <WhatsAppShare
            text={msg.content}
            sources={msg.sources}
          />

          {/* agent tags */}
          {msg.activatedAgents?.length > 0 && (
            <div className="ml-auto flex flex-wrap justify-end gap-1">
              {msg.activatedAgents
                .filter(a => a !== 'emergency')
                .map(a => (
                  <span key={a}
                    className="text-[9px] bg-gray-200 text-gray-500
                               rounded px-1.5 py-0.5 uppercase tracking-wide">
                    {a.replace('_', ' ')}
                  </span>
                ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ── helpers ─────────────────────────────────────────────── */

function MessageText({ text }) {
  // render newlines as paragraphs
  return (
    <div className="space-y-1.5">
      {text.split('\n').map((line, i) => {
        if (!line.trim()) return null
        // bold **text**
        const parts = line.split(/(\*\*[^*]+\*\*)/g)
        return (
          <p key={i}>
            {parts.map((part, j) =>
              part.startsWith('**') && part.endsWith('**')
                ? <strong key={j}>{part.slice(2, -2)}</strong>
                : part
            )}
          </p>
        )
      })}
    </div>
  )
}

function TTSButton({ text, lang }) {
  const [speaking, setSpeaking] = useState(false)

  const speak = () => {
    if (!('speechSynthesis' in window)) return

    if (speaking) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
      return
    }

    const utter = new SpeechSynthesisUtterance(text)
    utter.lang  = LANG_BCP47[lang] || 'en-IN'
    utter.rate  = 0.9

    utter.onstart = () => setSpeaking(true)
    utter.onend   = () => setSpeaking(false)
    utter.onerror = () => setSpeaking(false)

    window.speechSynthesis.speak(utter)
  }

  return (
    <button
      onClick={speak}
      className="flex items-center gap-1 text-[11px] text-gray-400
                 hover:text-emerald-600 transition-colors"
      title={speaking ? 'Stop' : 'Listen'}
    >
      {speaking
        ? <svg className="w-3.5 h-3.5" fill="currentColor"
            viewBox="0 0 24 24">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
          </svg>
        : <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24"
            stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round"
              strokeWidth={2}
              d="M15.536 8.464a5 5 0 010 7.072M12 6a7 7 0 010 12M8.464
                 8.464a5 5 0 000 7.072M6 12H4" />
          </svg>
      }
      Listen
    </button>
  )
}

function WhatsAppShare({ text, sources }) {
  const share = () => {
    const sourceList = sources?.length
      ? '\n\nSource: ' + sources.map(s => s.source).join(', ')
      : ''
    const msg     = encodeURIComponent(
      `SakhiBot says:\n\n${text}${sourceList}\n\nGet help: 181 (Women's Helpline)`
    )
    window.open(`https://wa.me/?text=${msg}`, '_blank')
  }

  return (
    <button
      onClick={share}
      className="flex items-center gap-1 text-[11px] text-gray-400
                 hover:text-green-600 transition-colors"
      title="Share on WhatsApp"
    >
      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099
                 -.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199
                 -.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883
                 -.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606
                 .134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099
                 -.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207
                 -.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01
                 -.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479
                 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077
                 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871
                 .118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289
                 .173-1.413-.074-.124-.272-.198-.57-.347z"/>
        <path d="M12 0C5.373 0 0 5.373 0 12c0 2.124.554 4.118 1.523 5.85
                 L0 24l6.335-1.507A11.95 11.95 0 0012 24c6.627 0 12-5.373
                 12-12S18.627 0 12 0zm0 22c-1.907 0-3.688-.497-5.23-1.367
                 l-.37-.22-3.861.918.936-3.752-.242-.385A9.953 9.953 0 012
                 12C2 6.486 6.486 2 12 2s10 4.486 10 10-4.486 10-10 10z"/>
      </svg>
      Share
    </button>
  )
}

const LANG_BCP47 = {
  en: 'en-IN',
  hi: 'hi-IN',
  bn: 'bn-IN',
  ta: 'ta-IN',
  te: 'te-IN',
  mr: 'mr-IN',
  gu: 'gu-IN',
  kn: 'kn-IN',
  ml: 'ml-IN',
}

