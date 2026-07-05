import { useEffect, useState } from 'react'
import LandingPage from './components/LandingPage'
import ChatWindow from './components/ChatWindow'
import InputBar from './components/InputBar'
import Login from './components/auth/Login'
import Signup from './components/auth/Signup'
import LanguageSelector from './components/LanguageSelector'
import PermissionManager from './components/PermissionManager'
import SOSButton from './components/SOSButton'
import {
  clearAuthToken,
  getCurrentUser,
  loginUser,
  saveAuthToken,
  sendMessage,
  signupUser,
} from './api'

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
  const [screen,   setScreen]   = useState('landing') // 'landing' | 'chat'
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [authChecking, setAuthChecking] = useState(() =>
    Boolean(localStorage.getItem('sakhibot_token'))
  )
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState('')
  const [authNotice, setAuthNotice] = useState('')
  const [user, setUser] = useState(null)
  const [isLogin, setIsLogin] = useState(true)
  const [lang, setLang] = useState('en')
  const [permissionGranted, setPermissionGranted] = useState(false)
  const [district,   setDistrict]   = useState('')   // eslint-disable-line
  const [stateName,  setStateName]  = useState('')   // eslint-disable-line

  // history for the API — role + content only
  const apiHistory = messages.map(m => ({
    role:    m.role,
    content: m.content,
  }))

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

    return () => {
      ignore = true
    }
  }, [])

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
      setIsLogin(true)
      setAuthNotice('Account created. Please login to continue.')
    } catch (err) {
      setAuthError(
        getErrorMessage(err, 'Signup failed. Please try again.')
      )
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
        message:   text,
        language:  lang,
        history:   apiHistory,
        district,
        stateName,
      })

      // update detected language
      if (data.detected_lang) setLang(data.detected_lang)

      // add bot reply
      setMessages(prev => [
        ...prev,
        {
          role:            'assistant',
          content:         data.answer,
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
          detectedLang:    data.detected_lang   || 'en',
        }
      ])
    } catch (err) {
      console.error(err)
      setMessages(prev => [
        ...prev,
        {
          role:    'assistant',
          content: 'Sorry, I could not connect to the server. '
                 + 'Please check your connection and try again. '
                 + 'For immediate help, call 181.',
          sources:     [],
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

  // AUTH SCREEN
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

  return (
    <div className="min-h-screen flex flex-col bg-white lg:bg-emerald-50/40">
      {/* header */}
<header className="border-b border-emerald-100/80 bg-white/95 sticky top-0 z-10 backdrop-blur">
  <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
    <div className="flex min-w-0 items-center gap-2.5">
      <button
        onClick={() => setScreen('landing')}
        className="w-9 h-9 bg-emerald-600 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-sm shrink-0"
        title="SakhiBot home"
      >
        S
      </button>

      <div>
        <h1 className="text-sm font-semibold text-gray-900 leading-none">
          SakhiBot
        </h1>

        <p className="text-[10px] text-gray-400 leading-none mt-0.5">
          Women's legal rights assistant
        </p>
      </div>
    </div>

    <div className="flex shrink-0 items-center gap-2">
      <LanguageSelector value={lang} onChange={setLang} />

      <button
        type="button"
        onClick={handleLogout}
        className="rounded-xl border border-gray-200 px-3 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-50"
      >
        Logout
      </button>

            {screen === 'chat' && (
              <button
                onClick={() => setScreen('landing')}
                className="text-gray-400 hover:text-gray-600 p-1"
title="Home"
>
  <svg
    className="w-5 h-5"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2
         2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0
         011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
    />
                </svg>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* content */}
      {!permissionGranted ? (
        <PermissionManager
          onComplete={handlePermissionComplete}
        />
      ) : screen === 'landing' ? (
        <LandingPage
          onStart={() => setScreen('chat')}
        />
      ) : (
<main
  className="mx-auto flex w-full max-w-4xl flex-1 flex-col bg-white
             shadow-sm lg:my-6 lg:min-h-[calc(100vh-6rem)]
             lg:rounded-3xl lg:border lg:border-emerald-100"
>
          <ChatWindow
            messages={messages}
            loading={loading}
            history={apiHistory}
          />

          <InputBar
            onSend={handleSend}
            loading={loading}
            lang={lang}
          />
        </main>
      )}

      {permissionGranted && <SOSButton />}
    </div>
  )
}

