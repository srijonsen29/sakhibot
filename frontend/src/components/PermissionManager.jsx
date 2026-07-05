import { useMemo, useState } from 'react'

export default function PermissionManager({ onComplete }) {
  const [permissions, setPermissions] = useState({
    location: false,
    camera: false,
    microphone: false,
  })
  const [error, setError] = useState('')

  const allGranted = useMemo(
    () => permissions.location && permissions.camera && permissions.microphone,
    [permissions]
  )

  const markGranted = key => {
    setError('')
    setPermissions(prev => ({
      ...prev,
      [key]: true,
    }))
  }

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setError('Location is not supported on this device.')
      return
    }

    navigator.geolocation.getCurrentPosition(
      position => {
        localStorage.setItem(
          'sakhibot_last_location',
          JSON.stringify({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: Math.round(position.coords.accuracy || 0),
            updatedAt: new Date().toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            }),
          })
        )
        markGranted('location')
      },
      () => setError('Location permission was denied. SOS needs location to share your position.'),
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 10000,
      }
    )
  }

  const requestCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      stream.getTracks().forEach(track => track.stop())
      markGranted('camera')
    } catch {
      setError('Camera permission was denied.')
    }
  }

  const requestMicrophone = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(track => track.stop())
      markGranted('microphone')
    } catch {
      setError('Microphone permission was denied.')
    }
  }

  const completePermissions = () => {
    onComplete?.()
  }

  const items = [
    {
      key: 'location',
      title: 'Location',
      description: 'Used by SOS to share your current position.',
      action: requestLocation,
    },
    {
      key: 'camera',
      title: 'Camera',
      description: 'Reserved for future SOS evidence capture.',
      action: requestCamera,
    },
    {
      key: 'microphone',
      title: 'Microphone',
      description: 'Reserved for future voice and SOS recording features.',
      action: requestMicrophone,
    },
  ]

  return (
    <main className="flex flex-1 items-center justify-center bg-emerald-50/70 px-4 py-8">
      <section className="w-full max-w-2xl rounded-3xl border border-emerald-100 bg-white p-6 shadow-xl sm:p-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Safety setup
          </p>
          <h1 className="mt-2 text-2xl font-bold text-gray-950">
            Allow essential permissions
          </h1>
          <p className="mt-3 text-sm leading-6 text-gray-500">
            These permissions help SakhiBot support emergency workflows when you
            use SOS.
          </p>
        </div>

        <div className="mt-6 space-y-3">
          {items.map(item => (
            <div
              key={item.key}
              className="flex flex-col gap-3 rounded-2xl border border-gray-100
                         bg-gray-50 p-4 sm:flex-row sm:items-center
                         sm:justify-between"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span
                    className={
                      permissions[item.key]
                        ? 'flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-xs font-bold text-white'
                        : 'flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs font-bold text-gray-400 ring-1 ring-gray-200'
                    }
                  >
                    {permissions[item.key] ? 'OK' : '-'}
                  </span>
                  <h2 className="text-sm font-bold text-gray-900">
                    {item.title}
                  </h2>
                </div>
                <p className="mt-1 pl-8 text-xs leading-5 text-gray-500">
                  {item.description}
                </p>
              </div>

              <button
                type="button"
                onClick={item.action}
                disabled={permissions[item.key]}
                className="rounded-xl bg-emerald-600 px-4 py-2.5 text-sm
                           font-bold text-white hover:bg-emerald-700
                           disabled:bg-emerald-100 disabled:text-emerald-700"
              >
                {permissions[item.key] ? 'Allowed' : 'Allow'}
              </button>
            </div>
          ))}
        </div>

        {error && (
          <p className="mt-4 rounded-2xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
            {error}
          </p>
        )}

        <button
          type="button"
          onClick={completePermissions}
          disabled={!allGranted}
          className="mt-6 w-full rounded-2xl bg-gray-950 px-5 py-3.5 text-sm
                     font-bold text-white hover:bg-black disabled:cursor-not-allowed
                     disabled:bg-gray-200 disabled:text-gray-500"
        >
          Continue to SakhiBot
        </button>
      </section>
    </main>
  )
}
