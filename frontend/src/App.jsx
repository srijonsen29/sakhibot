import { useEffect, useState, useCallback } from 'react'
import LandingPage       from './components/LandingPage'
import ChatWindow        from './components/ChatWindow'
import InputBar          from './components/InputBar'
import Login              from './components/auth/Login'
import Signup             from './components/auth/Signup'
import LanguageSelector  from './components/LanguageSelector'
import PermissionManager  from './components/PermissionManager'
import SOSButton          from './components/SOSButton'
import ConnectionBanner  from './components/ConnectionBanner'
import {
  clearAuthToken,
  getCurrentUser,
  loginUser,
  saveAuthToken,
  sendMessage,
  signupUser,
  healthCheck,
} from './api'

const permissionKeyFor = user => `sakhibot_permissions_${user.id}`

function getErrorMessage(err, fallback) {
  const detail = err.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return fallback
}

export default function App() {
  // ── screen / chat state ──────────────────────────────────────────────
  const [screen,         setScreen]         = useState('landing') // 'landing' | 'chat'
  const [messages,       setMessages]       = useState([])
  const [loading,        setLoading]        = useState(false)
  const [lang,           setLang]           = useState('en')
  const [district,       setDistrict]       = useState('')
  const [stateName,      setStateName]      = useState('')
  const [askingLocation, setAskingLocation] = useState(false)
  const [serverDown,     setServerDown]     = useState(false)

  // ── auth state ────────────────────────────────────────────────────────
  const [authChecking, setAuthChecking] = useState(() =>
    Boolean(localStorage.getItem('sakhibot_token'))
  )
  const [authLoading, setAuthLoading] = useState(false)
  const [authError,   setAuthError]   = useState('')
  const [authNotice,  setAuthNotice]  = useState('')
  const [user,        setUser]        = useState(null)
  const [isLogin,     setIsLogin]     = useState(true)
  const [permissionGranted, setPermissionGranted] = useState(false)

  const apiHistory = messages.map(m => ({
    role: m.role, content: m.content,
  }))

  // ── verify saved auth token on first load ──────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem('sakhibot_token')
    if (!token) return

    let ignore = false

    async function verifySavedToken() {
      try {
        const currentUser = await getCurrentUser()
        if (ignore) return
        setUser(currentUser)
        setPermissionGranted(
          Boolean(localStorage.getItem(permissionKeyFor(currentUser)))
        )
      } catch {
        clearAuthToken()
      } finally {
        if (!ignore) setAuthChecking(false)
      }
    }

    verifySavedToken()
    return () => { ignore = true }
  }, [])

  // ── auth handlers ────────────────────────────────────────────────────
  const handleLogin = async credentials => {
    setAuthError('')
    setAuthNotice('')
    setAuthLoading(true)
    try {
      const data = await loginUser(credentials)
      saveAuthToken(data.access_token)
      setUser(data.user)
      setPermissionGranted(
        Boolean(localStorage.getItem(permissionKeyFor(data.user)))
      )
    } catch (err) {
      setAuthError(getErrorMessage(err, 'Login failed. Please try again.'))
    } finally {
      setAuthLoading(false)
    }
  }

  const handleSignup = async payload => {
    setAuthError('')
    setAuthNotice('')
    setAuthLoading(true)
    try {
      await signupUser(payload)
      setIsLogin(true)
      setAuthNotice('Account created. Please login to continue.')
    } catch (err) {
      setAuthError(getErrorMessage(err, 'Signup failed. Please try again.'))
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    clearAuthToken()
    setUser(null)
    setMessages([])
    setPermissionGranted(false)
    setIsLogin(true)
    setScreen('landing')
  }

  const handlePermissionComplete = () => {
    if (user) {
      localStorage.setItem(permissionKeyFor(user), 'granted')
    }
    setPermissionGranted(true)
  }

  // ── chat handlers ─────────────────────────────────────────────────────
  const checkServer = useCallback(async () => {
    try { await healthCheck(); setServerDown(false) }
    catch { setServerDown(true) }
  }, [])

  const handleSend = useCallback(async (text) => {
    if (!text.trim() || loading) return
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    setAskingLocation(false)

    try {
      const data = await sendMessage({
        message: text, language: lang,
        history: apiHistory, district, stateName,
      })
      setServerDown(false)
      if (data.detected_lang) setLang(data.detected_lang)

      setMessages(prev => [...prev, {
        role:            'assistant',
        content:         data.answer          || '',
        sources:         data.sources         || [],
        resources:       data.resources       || [],
        helplines:       data.helplines       || [],
        safetyPlan:      data.safety_plan     || [],
        documentReady:   data.document_ready  || false,
        documentType:    data.document_type   || '',
        nextQuestion:    data.next_question   || '',
        isEmergency:     data.is_emergency    || false,
        severity:        data.severity        || 'none',
        activatedAgents: data.activated_agents|| [],
        detectedLang:    data.detected_lang   || lang,
        askingLocation:  data.asking_location || false,
      }])

      if (data.asking_location) setAskingLocation(true)

    } catch (err) {
      console.error('Send failed:', err)
      setServerDown(true)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Could not connect to server. Please check your connection. For immediate help call 181.',
        sources: [], isEmergency: false,
      }])
    } finally {
      setLoading(false)
    }
  }, [loading, lang, apiHistory, district, stateName])

  const handleLocationSubmit = useCallback((d, s) => {
    setDistrict(d); setStateName(s); setAskingLocation(false)
    handleSend(`I am in ${d}, ${s}. Please show me the nearest resources.`)
  }, [handleSend])

  const startChat = useCallback(async () => {
    setScreen('chat')
    try { await healthCheck(); setServerDown(false) }
    catch { setServerDown(true) }
  }, [])

  // ── auth gating screens ──────────────────────────────────────────────
  if (authChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-emerald-50 px-4">
        <div className="rounded-3xl border border-emerald-100 bg-white px-6 py-5 text-sm font-semibold text-emerald-700 shadow-xl">
          Checking your session...
        </div>
      </div>
    )
  }

  if (!user) {
    return isLogin ? (
      <Login
        loading={authLoading}
        error={authError}
        notice={authNotice}
        onSwitch={() => {
          setAuthError('')
          setAuthNotice('')
          setIsLogin(false)
        }}
        onLogin={handleLogin}
      />
    ) : (
      <Signup
        loading={authLoading}
        error={authError}
        onSwitch={() => {
          setAuthError('')
          setAuthNotice('')
          setIsLogin(true)
        }}
        onSignup={handleSignup}
      />
    )
  }

  if (!permissionGranted) {
    return <PermissionManager onComplete={handlePermissionComplete} />
  }

  // ── main responsive app ───────────────────────────────────────────────
  return (
    <div className="h-screen flex flex-col lg:flex-row bg-gray-50
                    overflow-hidden">

      {/* ── DESKTOP SIDEBAR (hidden on mobile) ──────────────────────── */}
      <aside className="hidden lg:flex lg:flex-col lg:w-80 xl:w-96
                        bg-white border-r border-gray-100 shrink-0
                        overflow-y-auto">
        <DesktopSidebar
          onStart={startChat}
          screen={screen}
          lang={lang}
          setLang={setLang}
          onLogout={handleLogout}
        />
      </aside>

      {/* ── MAIN AREA ────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* Mobile header — hidden on desktop */}
        <header className="lg:hidden flex items-center justify-between
                           px-4 py-3 bg-white border-b border-gray-100
                           shrink-0">
          <button
            onClick={() => setScreen(screen === 'chat' ? 'landing' : 'chat')}
            className="flex items-center gap-2.5"
          >
            <div className="w-8 h-8 bg-emerald-600 rounded-full flex
                            items-center justify-center text-white
                            text-sm font-bold">
              S
            </div>
            <div>
              <h1 className="text-sm font-semibold text-gray-900 leading-none">
                SakhiBot
              </h1>
              <p className="text-[10px] text-gray-400 leading-none mt-0.5">
                Women's legal rights
              </p>
            </div>
          </button>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${serverDown
              ? 'bg-red-400 animate-pulse' : 'bg-emerald-400'}`} />
            <LanguageSelector value={lang} onChange={setLang} />
            <button
              type="button"
              onClick={handleLogout}
              className="text-xs text-gray-400 hover:text-gray-600 px-1"
            >
              Logout
            </button>
            <a href="tel:181"
              className="text-xs bg-red-50 text-red-600 border border-red-200
                         rounded-full px-2.5 py-1 font-medium">
              181
            </a>
          </div>
        </header>

        {/* Desktop chat header */}
        {screen === 'chat' && (
          <div className="hidden lg:flex items-center justify-between
                          px-6 py-3 bg-white border-b border-gray-100 shrink-0">
            <div>
              <h2 className="text-sm font-semibold text-gray-800">
                Chat with SakhiBot
              </h2>
              <p className="text-xs text-gray-400">
                {messages.length > 0
                  ? `${messages.length} messages`
                  : 'Ask anything about your rights'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className={`flex items-center gap-1.5 text-xs
                              ${serverDown ? 'text-red-500' : 'text-emerald-600'}`}>
                <div className={`w-1.5 h-1.5 rounded-full
                                 ${serverDown
                                   ? 'bg-red-400 animate-pulse'
                                   : 'bg-emerald-400'}`} />
                {serverDown ? 'Disconnected' : 'Connected'}
              </div>
              <LanguageSelector value={lang} onChange={setLang} />
            </div>
          </div>
        )}

        {/* Server down banner */}
        {serverDown && screen === 'chat' && (
          <ConnectionBanner onRetry={checkServer} />
        )}

        {/* Content */}
        {screen === 'landing' ? (
          <div className="flex-1 overflow-y-auto lg:hidden">
            <LandingPage onStart={startChat} />
          </div>
        ) : (
          <>
            <ChatWindow
              messages={messages}
              loading={loading}
              history={apiHistory}
              askingLocation={askingLocation}
              onLocationSubmit={handleLocationSubmit}
            />
            <InputBar
              onSend={handleSend}
              loading={loading}
              lang={lang}
            />
          </>
        )}

        {/* Desktop landing — show in main area when no chat yet */}
        {screen === 'landing' && (
          <div className="hidden lg:flex flex-1 items-center
                          justify-center bg-gray-50">
            <DesktopWelcome onStart={startChat} />
          </div>
        )}
      </div>

      <SOSButton />
    </div>
  )
}

/* ── Desktop Sidebar ────────────────────────────────────────────────────── */
function DesktopSidebar({ onStart, screen, lang, setLang, onLogout }) {
  const FEATURES = [
    { icon: '⚖️', label: 'Legal answers',   sub: 'DV Act, POSH, IPC 498A'     },
    { icon: '📄', label: 'FIR drafts',       sub: 'Complaint letters'           },
    { icon: '📍', label: 'Nearby shelters',  sub: 'One Stop Centres'            },
    { icon: '🗺️', label: 'Safety plan',      sub: 'Step-by-step guidance'       },
  ]

  return (
    <div className="flex flex-col h-full">

      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-600 rounded-xl flex
                            items-center justify-center text-white
                            font-bold text-lg shrink-0">
              S
            </div>
            <div>
              <h1 className="text-base font-semibold text-gray-900">
                SakhiBot
              </h1>
              <p className="text-xs text-gray-400">
                Women's legal rights assistant
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="text-xs text-gray-400 hover:text-gray-600
                       border border-gray-200 rounded-lg px-2.5 py-1.5"
          >
            Logout
          </button>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full
                           animate-pulse" />
          <span className="text-xs text-gray-500">
            Free · No login fee · Always available
          </span>
        </div>
      </div>

      {/* Tagline */}
      <div className="px-6 py-5 border-b border-gray-100">
        <h2 className="text-xl font-semibold text-gray-900 leading-snug mb-1">
          Aapka haq,{' '}
          <span className="text-emerald-600">aapki bhasha mein</span>
        </h2>
        <p className="text-sm text-gray-500 leading-relaxed">
          Know your legal rights in 9 Indian languages. Answers
          from real Indian law — always cited.
        </p>
      </div>

      {/* Features */}
      <div className="px-6 py-4 border-b border-gray-100">
        <p className="text-xs font-semibold text-gray-400 uppercase
                      tracking-wider mb-3">
          What I can do
        </p>
        <div className="space-y-3">
          {FEATURES.map((f, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="text-xl w-7 shrink-0">{f.icon}</span>
              <div>
                <p className="text-sm font-medium text-gray-800">
                  {f.label}
                </p>
                <p className="text-xs text-gray-400">{f.sub}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Languages */}
      <div className="px-6 py-4 border-b border-gray-100">
        <p className="text-xs font-semibold text-gray-400 uppercase
                      tracking-wider mb-2">
          Language
        </p>
        <LanguageSelector value={lang} onChange={setLang} />
        <p className="text-xs text-gray-400 mt-2">
          Auto-detected from your message
        </p>
      </div>

      {/* Stats */}
      <div className="px-6 py-4 border-b border-gray-100">
        <div className="grid grid-cols-2 gap-3">
          {[
            ['9',    'Languages'],
            ['8+',   'Legal Acts'],
            ['4',    'AI Agents'],
            ['24/7', 'Available'],
          ].map(([num, label]) => (
            <div key={label}
              className="bg-gray-50 rounded-xl p-3 text-center border
                         border-gray-100">
              <p className="text-lg font-semibold text-emerald-600">
                {num}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA buttons */}
      <div className="px-6 py-4 mt-auto space-y-2">
        {screen !== 'chat' && (
          <button
            onClick={onStart}
            className="w-full bg-emerald-600 hover:bg-emerald-700
                       text-white font-medium rounded-xl py-3 text-sm
                       transition-colors"
          >
            Start asking →
          </button>
        )}

        <a href="tel:181"
          className="w-full flex items-center justify-center gap-2
                     border-2 border-red-200 text-red-600 rounded-xl
                     py-2.5 text-sm font-medium hover:bg-red-50
                     transition-colors"
          >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3
                     .7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0
                     .6-.4 1-1 1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c
                     .6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2
                     1L6.6 10.8z"/>
          </svg>
          Emergency — Call 181
        </a>
      </div>
    </div>
  )
}

/* ── Desktop Welcome (center area before chat starts) ───────────────────── */
function DesktopWelcome({ onStart }) {
  const STEPS = [
    {
      icon: '💬',
      title: 'Ask in your language',
      desc: 'Type or speak in Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam or English'
    },
    {
      icon: '⚖️',
      title: 'Get grounded answers',
      desc: 'Every answer comes from real Indian laws — DV Act, POSH, IPC 498A, Constitution and more. Always cited.'
    },
    {
      icon: '✅',
      title: 'Take action',
      desc: 'Download a complaint letter, find the nearest shelter, get a step-by-step safety plan'
    },
  ]

  return (
    <div className="max-w-lg w-full px-8 py-12 text-center">
      <div className="w-20 h-20 bg-emerald-100 rounded-2xl flex items-center
                      justify-center mx-auto mb-6">
        <svg className="w-10 h-10 text-emerald-600" fill="none"
          viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03
               8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72
               C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9
               3.582 9 8z" />
        </svg>
      </div>

      <h2 className="text-2xl font-semibold text-gray-900 mb-2">
        How can I help you today?
      </h2>
      <p className="text-gray-500 text-sm leading-relaxed mb-8">
        Ask me anything about your legal rights. I answer from real
        Indian law in your language.
      </p>

      <div className="space-y-4 mb-8 text-left">
        {STEPS.map((s, i) => (
          <div key={i}
            className="flex gap-4 bg-white rounded-xl p-4 border
                       border-gray-100 shadow-sm">
            <span className="text-2xl shrink-0">{s.icon}</span>
            <div>
              <p className="text-sm font-semibold text-gray-800 mb-0.5">
                {s.title}
              </p>
              <p className="text-xs text-gray-500 leading-relaxed">
                {s.desc}
              </p>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={onStart}
        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white
                   font-semibold rounded-2xl py-4 text-base transition-colors
                   shadow-sm"
      >
        Start asking →
      </button>

      <div className="flex flex-wrap justify-center gap-2 mt-4">
        {[
          'What is domestic violence?',
          'मुझे मदद चाहिए',
          'How to file FIR?',
          'POSH Act rights',
        ].map((s, i) => (
          <span key={i}
            className="text-xs bg-white border border-gray-200
                       text-gray-500 rounded-full px-3 py-1.5 shadow-sm">
            {s}
          </span>
        ))}
      </div>
    </div>
  )
}
