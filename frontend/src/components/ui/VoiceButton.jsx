import { useState, useRef } from 'react'

const LANG_BCP47 = {
  en: 'en-IN', hi: 'hi-IN', bn: 'bn-BD', ta: 'ta-IN',
  te: 'te-IN', mr: 'mr-IN', gu: 'gu-IN', kn: 'kn-IN', ml: 'ml-IN',
}

export default function VoiceButton({ lang = 'en', onResult, disabled }) {
  const [listening, setListening] = useState(false)
  const recognizerRef = useRef(null)

  const supported = 'SpeechRecognition' in window ||
                    'webkitSpeechRecognition' in window

  const toggle = () => {
    if (!supported) {
      alert('Voice input is not supported in this browser. Please use Chrome.')
      return
    }

    if (listening) {
      recognizerRef.current?.stop()
      setListening(false)
      return
    }

    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    const rec = new SR()
    rec.lang          = LANG_BCP47[lang] || 'en-IN'
    rec.interimResults = false
    rec.maxAlternatives = 1

    rec.onstart  = () => setListening(true)
    rec.onend    = () => setListening(false)
    rec.onerror  = () => setListening(false)
    rec.onresult = e => {
      const transcript = e.results[0][0].transcript
      if (transcript) onResult(transcript)
    }

    recognizerRef.current = rec
    rec.start()
  }

  return (
    <button
      onClick={toggle}
      disabled={disabled || !supported}
      title={listening ? 'Tap to stop' : 'Tap to speak'}
      className={`w-10 h-10 rounded-full flex items-center justify-center
                  transition-all shrink-0 disabled:opacity-40
                  ${listening
                    ? 'bg-red-100 text-red-600 animate-pulse'
                    : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'
                  }`}
    >
      {listening
        ? <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2a3 3 0 013 3v7a3 3 0 01-6 0V5a3 3 0 013-3zm7
                     10a7 7 0 01-14 0H3a9 9 0 0018 0h-2z"/>
            <rect x="11" y="19" width="2" height="4"/>
            <rect x="8" y="22" width="8" height="2"/>
          </svg>
        : <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24"
            stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0
                 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0
                 01-3 3z" />
          </svg>
      }
    </button>
  )
}