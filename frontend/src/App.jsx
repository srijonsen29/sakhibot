import { useEffect, useState } from 'react'
import LandingPage from './components/ui/LandingPage'
import ChatWindow from './components/chat/ChatWindow'
import InputBar from './components/chat/InputBar'
import Login from './components/auth/Login'
import Signup from './components/auth/Signup'
import EmergencySetup from './components/auth/EmergencySetup'
import EmergencyContactManager from './components/emergency/EmergencyContactManager'
import LanguageSelector from './components/ui/LanguageSelector'
import PermissionManager from './components/ui/PermissionManager'
import SOSButton from './components/emergency/SOSButton'
import {
  clearAuthToken,
  getCurrentUser,
  loginUser,
  saveAuthToken,
  sendMessage,
  signupUser,
  setupEmergencyContacts,
} from './api'

const BYPASS_AUTH = import.meta.env.VITE_BYPASS_AUTH === 'true'
console.log('BYPASS_AUTH:', BYPASS_AUTH)
const permissionKeyFor = user => `sakhibot_permissions_${user.id}`

function getErrorMessage(err, fallback) {
  const detail = err.response?.data?.detail

  if (typeof detail === 'string') return detail

  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg
  }

  return fallback
}

export default function App() {
  const [screen, setScreen] = useState('landing') // 'landing' | 'chat' | 'sos'
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [authChecking, setAuthChecking] = useState(() =>
    BYPASS_AUTH || Boolean(localStorage.getItem('sakhibot_token'))
  )
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authNotice, setAuthNotice] = useState('')
  const [user, setUser] = useState(null)
  // 'login' | 'signup-1' | 'signup-2'
  const [authScreen, setAuthScreen] = useState('login')
  const [lang, setLang] = useState('en')
  const [permissionGranted, setPermissionGranted] = useState(false)
  const [district, setDistrict] = useState('')   // eslint-disable-line
  const [stateName, setStateName] = useState('')   // eslint-disable-line
  const [showContactManager, setShowContactManager] = useState(false)

  // history for the API — role + content only
  const apiHistory = messages.map(m => ({
    role: m.role,
    content: m.content,
  }))

  // ── push initial history state ────────────────────────────────────────────
  useEffect(() => {
    window.history.replaceState({ type: 'auth', authScreen: 'login' }, '')
  }, [])

  // ── listen for browser back/forward ──────────────────────────────────────
  useEffect(() => {
    const onPop = e => {
      const state = e.state
      if (!state) return
      if (state.type === 'auth') {
        setAuthScreen(state.authScreen)
      } else if (state.type === 'app') {
        setScreen(state.screen)
      }
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  // ── navigate app screens with history ────────────────────────────────────
  const goToScreen = scr => {
    setScreen(scr)
    window.history.pushState({ type: 'app', screen: scr }, '')
  }

  // ── verify existing token on load (or log in as the dev bypass user) ─────
  useEffect(() => {
    const token = localStorage.getItem('sakhibot_token')
    if (!token && !BYPASS_AUTH) return

    let ignore = false

    async function verifySavedToken() {
      try {
        const currentUser = await getCurrentUser()
        if (ignore) return

        setUser(currentUser)
        setPermissionGranted(
          Boolean(localStorage.getItem(permissionKeyFor(currentUser)))
        )
        window.history.replaceState({ type: 'app', screen: 'landing' }, '')
      } catch {
        clearAuthToken()
      } finally {
        if (!ignore) setAuthChecking(false)
      }
    }

    verifySavedToken()

    return () => {
      ignore = true
    }
  }, [])

  // ── helper: navigate auth screens with history entry ─────────────────────
  const goToAuthScreen = screen => {
    setAuthScreen(screen)
    setAuthError('')
    setAuthNotice('')
    window.history.pushState({ type: 'auth', authScreen: screen }, '')
  }

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
      window.history.replaceState({ type: 'app', screen: 'landing' }, '')
    } catch (err) {
      setAuthError(
        getErrorMessage(err, 'Login failed. Please try again.')
      )
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
      goToAuthScreen('login')
      setAuthNotice('Account created! Please login to continue.')
    } catch (err) {
      setAuthError(
        getErrorMessage(err, 'Signup failed. Please try again.')
      )
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    if (user) {
      localStorage.removeItem(permissionKeyFor(user))  // reset so location page shows on next login
    }
    clearAuthToken()
    setUser(null)
    setMessages([])
    setPermissionGranted(false)
    setAuthScreen('login')
    window.history.replaceState({ type: 'auth', authScreen: 'login' }, '')
  }


  const handlePermissionComplete = () => {
    if (user) {
      localStorage.setItem(permissionKeyFor(user), 'granted')
    }
    setPermissionGranted(true)
  }

  const handleSend = async text => {
    if (!text.trim() || loading) return

    // add user message instantly
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const data = await sendMessage({
        message: text,
        language: lang,
        history: apiHistory,
        district,
        stateName,
      })

      // update detected language
      if (data.detected_lang) setLang(data.detected_lang)

      // add bot reply
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
          resources: data.resources || [],
          helplines: data.helplines || [],
          safetyPlan: data.safety_plan || [],
          documentReady: data.document_ready || false,
          documentType: data.document_type || '',
          documentForm: data.document_form || null,
          nextQuestion: data.next_question || '',
          isEmergency: data.is_emergency || false,
          severity: data.severity || 'none',
          activatedAgents: data.activated_agents || [],
          detectedLang: data.detected_lang || 'en',
        }
      ])
    } catch (err) {
      console.error(err)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I could not connect to the server. '
            + 'Please check your connection and try again. '
            + 'For immediate help, call 181.',
          sources: [],
          isEmergency: false,
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  if (authChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-emerald-50 px-4">
        <div className="rounded-3xl border border-emerald-100 bg-white px-6 py-5 text-sm font-semibold text-emerald-700 shadow-xl">
          Checking your session...
        </div>
      </div>
    )
  }

  const handleEmergencySetupComplete = async activeContacts => {
    await setupEmergencyContacts(activeContacts)
    // Refresh user state
    const currentUser = await getCurrentUser()
    setUser(currentUser)
  }

  // AUTH SCREEN
  if (!user) {
    if (authScreen === 'login') {
      return (
        <Login
          loading={authLoading}
          error={authError}
          notice={authNotice}
          onSwitch={() => goToAuthScreen('signup-1')}
          onLogin={handleLogin}
        />
      )
    }
    return (
      <Signup
        loading={authLoading}
        error={authError}
        initialStep={authScreen === 'signup-2' ? 2 : 1}
        onStepChange={step => goToAuthScreen(step === 2 ? 'signup-2' : 'signup-1')}
        onSwitch={() => goToAuthScreen('login')}
        onSignup={handleSignup}
      />
    )
  }

  // EMERGENCY SETUP REDIRECT SCREEN
  if (!user.has_emergency_contacts) {
    return (
      <EmergencySetup
        onComplete={handleEmergencySetupComplete}
      />
    )
  }


  return (
    <div className="min-h-screen flex flex-col bg-white lg:bg-emerald-50/40">
      {/* header */}
      <header className="border-b border-emerald-100/80 bg-white/95 sticky top-0 z-10 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-2.5">
            <button
              onClick={() => goToScreen('landing')}
              className="w-9 h-9 bg-emerald-600 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-sm shrink-0"
              title="SakhiBot home"
            >
              S
            </button>

            <div>
              <h1 className="text-sm font-semibold text-gray-900 leading-none">
                SakhiBot
              </h1>
            </div>
          </div >

          <div className="flex shrink-0 items-center gap-2">
            <LanguageSelector value={lang} onChange={setLang} />

            {screen !== 'landing' && (
              <button
                type="button"
                onClick={() => setShowContactManager(true)}
                className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-100"
              >
                Contacts
              </button>
            )}

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-xl border border-gray-200 px-3 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-50"
            >
              Logout
            </button>

            {user && (
              <div className="flex flex-col items-center justify-center gap-1 px-1">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-emerald-200 bg-emerald-50 text-emerald-700">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </span>
                <span className="max-w-[7rem] truncate text-xs font-semibold text-emerald-700 text-center">
                  {user.name}
                </span>
              </div>
            )}

            {screen === 'chat' && (
              <button
                onClick={() => goToScreen('landing')}
                className="text-gray-400 hover:text-gray-600 p-1"
                title="Home"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </button>
            )
            }
          </div >
        </div >
      </header >

      {/* content */}
      {
        !permissionGranted ? (
          <PermissionManager onComplete={handlePermissionComplete} />
        ) : screen === 'landing' || screen === 'sos' ? (
          <LandingPage
            onStart={() => goToScreen('chat')}
            onSOS={() => goToScreen('sos')}
            onContacts={() => setShowContactManager(true)}
          />
        ) : (
          <main
            className="mx-auto flex w-full max-w-4xl flex-1 flex-col bg-white
                     shadow-sm lg:my-6 lg:min-h-[calc(100vh-6rem)]
                     lg:rounded-3xl lg:border lg:border-emerald-100"
          >
            <ChatWindow messages={messages} loading={loading} history={apiHistory} />
            <InputBar onSend={handleSend} loading={loading} lang={lang} />
          </main>
        )}

      {/* Single SOSButton — forceOpen when screen==='sos' so it auto-opens */}
      {permissionGranted && (
        <SOSButton
          forceOpen={screen === 'sos'}
          onForceClose={() => goToScreen('landing')}
        />
      )
      }
      {showContactManager && (
        <EmergencyContactManager
          onClose={() => setShowContactManager(false)}
          onSaved={async () => setUser(await getCurrentUser())}
        />
      )}
    </div >
  )
}
