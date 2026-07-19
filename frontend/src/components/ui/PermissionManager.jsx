import { useState } from 'react'

export default function PermissionManager({ onComplete }) {
  const [status, setStatus] = useState('idle')   // 'idle' | 'requesting' | 'granted' | 'denied'
  const [error, setError] = useState('')

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setError('Location is not supported on this device.')
      return
    }
    setStatus('requesting')
    setError('')

    navigator.geolocation.getCurrentPosition(
      position => {
        localStorage.setItem(
          'sakhibot_last_location',
          JSON.stringify({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: Math.round(position.coords.accuracy || 0),
            updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          })
        )
        setStatus('granted')
      },
      () => {
        setStatus('denied')
        setError('Location access was denied. Please allow it in your browser settings and try again.')
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
    )
  }

  const isGranted = status === 'granted'
  const isDenied = status === 'denied'
  const isWaiting = status === 'requesting'

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">

        {/* card */}
        <div className="rounded-3xl bg-white shadow-xl border border-emerald-100 overflow-hidden">

          {/* top banner */}
          <div className="bg-gradient-to-r from-emerald-700 to-emerald-600 px-8 py-8 text-center relative">
            {/* pulse rings */}
            <div className="relative inline-flex items-center justify-center mx-auto mb-4">
              {isGranted ? null : (
                <>
                  <span className="absolute inline-flex h-20 w-20 rounded-full bg-white/20 animate-ping" />
                  <span className="absolute inline-flex h-16 w-16 rounded-full bg-white/20 animate-ping" style={{ animationDelay: '0.3s' }} />
                </>
              )}
              <div className={`relative h-16 w-16 rounded-full flex items-center justify-center transition-colors duration-500 ${isGranted ? 'bg-white' : isDenied ? 'bg-red-100' : 'bg-white/20'
                }`}>
                {isGranted ? (
                  <svg className="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : isDenied ? (
                  <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : (
                  <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round"
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                )}
              </div>
            </div>

            <h1 className="text-2xl font-bold text-white">
              {isGranted ? 'Location Enabled!' : isDenied ? 'Access Denied' : 'Enable Location Access'}
            </h1>
            <p className="mt-1 text-sm text-emerald-100">
              {isGranted
                ? 'Your safety is our priority'
                : 'Required for SOS emergency features'}
            </p>
          </div>

          {/* body */}
          <div className="px-8 py-6 space-y-5">

            {/* why we need it */}
            {!isGranted && (
              <div className="space-y-3">
                <p className="text-xs font-bold uppercase tracking-widest text-gray-400">Why we need this</p>
                {[
                  { icon: '🆘', title: 'Emergency SOS', desc: 'Instantly share your exact location with emergency contacts when you press SOS' },
                  { icon: '🚔', title: 'Nearby Police', desc: 'Find the closest police stations and women\'s help centres near you' },
                  { icon: '🛡️', title: 'Safety Planning', desc: 'Get location-aware safety guidance and shelter recommendations' },
                ].map(item => (
                  <div key={item.title} className="flex gap-3 rounded-2xl bg-gray-50 border border-gray-100 px-4 py-3">
                    <span className="text-xl shrink-0">{item.icon}</span>
                    <div>
                      <p className="text-sm font-semibold text-gray-800">{item.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5 leading-4">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* granted state */}
            {isGranted && (
              <div className="rounded-2xl bg-white border border-emerald-100 px-5 py-4 flex gap-4 items-start">
                <span className="text-2xl">📍</span>
                <div>
                  <p className="font-bold text-emerald-800 text-sm">Location access granted</p>
                  <p className="text-xs text-emerald-700 mt-1 leading-5">
                    SakhiBot can now share your real-time location with your emergency contacts when you trigger an SOS.
                  </p>
                </div>
              </div>
            )}

            {/* error */}
            {error && (
              <div className="rounded-2xl bg-red-50 border border-red-200 px-4 py-3">
                <p className="text-sm font-semibold text-red-700">⚠️ {error}</p>
                <p className="text-xs text-red-600 mt-1">
                  To fix: Click the 🔒 lock icon in your browser's address bar → Site Settings → Location → Allow
                </p>
              </div>
            )}

            {/* privacy note */}
            <div className="rounded-2xl bg-amber-50 border border-amber-100 px-4 py-3 flex gap-2">
              <span className="text-sm shrink-0">🔒</span>
              <p className="text-xs text-amber-800 leading-5">
                <strong>Your privacy is protected.</strong> Your location is <em>never</em> shared or stored without your explicit action. It is only used when you press the SOS button.
              </p>
            </div>

            {/* action button */}
            {!isGranted ? (
              <button
                type="button"
                onClick={requestLocation}
                disabled={isWaiting}
                className="w-full rounded-2xl bg-emerald-600 py-4 font-bold text-white text-base
                           hover:bg-emerald-700 active:scale-95 transition-colors duration-150
                           disabled:bg-emerald-300 disabled:cursor-wait shadow-sm"
              >
                {isWaiting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Waiting for permission…
                  </span>
                ) : isDenied ? (
                  '🔄  Try Again'
                ) : (
                  '📍  Allow Location Access'
                )}
              </button>
            ) : (
              <button
                type="button"
                onClick={() => onComplete?.()}
                className="w-full rounded-2xl bg-gray-950 py-4 font-bold text-white text-base
                           hover:bg-black active:scale-95 transition-colors duration-150 shadow-sm"
              >
                Continue to SakhiBot →
              </button>
            )}

            {/* step hint shown before granting */}
            {status === 'idle' && (
              <p className="text-center text-xs text-gray-400">
                A browser popup will appear — click <strong className="text-gray-600">"Allow"</strong> to enable location
              </p>
            )}

          </div>
        </div>

        {/* SakhiBot branding below card */}
        <p className="mt-4 text-center text-xs text-gray-400">
          SakhiBot · AI-powered Women's Legal Rights Assistant · India
        </p>

      </div>
    </div>
  )
}

