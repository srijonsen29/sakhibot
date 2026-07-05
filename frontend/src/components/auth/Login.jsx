import { useState } from 'react'

export default function Login({ error = '', loading = false, notice = '', onSwitch, onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = e => {
    e.preventDefault()

    onLogin({
      email,
      password,
    })
  }

  return (
    <div className="min-h-screen bg-emerald-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-3xl bg-white shadow-xl border border-emerald-100 p-8">

        <div className="text-center">
          <h1 className="text-3xl font-bold text-emerald-700">
            SakhiBot
          </h1>

          <p className="mt-2 text-gray-500">
            Welcome back
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          {notice && (
            <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
              {notice}
            </p>
          )}

          {error && (
            <p className="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
              {error}
            </p>
          )}

          <div>
            <label className="text-sm font-medium text-gray-700">
              Email
            </label>

            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">
              Password
            </label>

            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-wait disabled:bg-emerald-300"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>

          <p className="text-center text-sm text-gray-500">
            New user?{' '}
            <button
              type="button"
              onClick={onSwitch}
              className="text-emerald-600 font-semibold"
            >
              Create account
            </button>
          </p>

        </form>
      </div>
    </div>
  )
}
