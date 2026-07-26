import { useState } from 'react'

// ── Must match backend VALID_RELATIONSHIPS list ────────────────────────────
const RELATIONSHIPS = [
  'Mother', 'Father', 'Sister', 'Brother',
  'Husband', 'Friend', 'Neighbor', 'Colleague',
  'Aunt', 'Uncle', 'Cousin', 'Guardian', 'Other',
]

const EMPTY_CONTACT = { name: '', phone: '', relationship: '' }

function validateContact(contact) {
  const errors = {}
  const nameClean = contact.name.trim()
  const phoneClean = contact.phone.trim()

  if (nameClean.length < 2) {
    errors.name = 'Name must be at least 2 characters'
  } else if (!/^[A-Za-z\s]+$/.test(nameClean)) {
    errors.name = 'Name must contain only letters and spaces'
  }

  if (!/^\d{10}$/.test(phoneClean)) {
    errors.phone = 'Phone number must be exactly 10 digits'
  }

  if (!contact.relationship) {
    errors.relationship = 'Please select a relationship'
  }

  return errors
}

export default function Signup({ error = '', loading = false, initialStep = 1, onStepChange, onSwitch, onSignup }) {
  const [step, setStep] = useState(initialStep)

  // Step 1 — account fields
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [step1Error, setStep1Error] = useState('')

  // Step 2 — 3 emergency contacts
  const [contacts, setContacts] = useState([
    { ...EMPTY_CONTACT },
    { ...EMPTY_CONTACT },
    { ...EMPTY_CONTACT },
  ])
  const [contactErrors, setContactErrors] = useState([{}, {}, {}])

  // ── step 1 validation ──────────────────────────────────────────────────────
  const handleNext = e => {
    e.preventDefault()
    setStep1Error('')
    if (name.trim().length < 2) {
      setStep1Error('Full name must be at least 2 characters')
      return
    }
    if (!email.includes('@') || !email.split('@')[1]?.includes('.')) {
      setStep1Error('Please enter a valid email address')
      return
    }
    if (password.length < 6) {
      setStep1Error('Password must be at least 6 characters')
      return
    }
    setStep(2)
    onStepChange?.(2)
  }

  // ── update a single contact field ──────────────────────────────────────────
  const updateContact = (index, field, value) => {
    setContacts(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
    // clear error for that field on change
    setContactErrors(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: '' }
      return updated
    })
  }

  // ── step 2 submit ──────────────────────────────────────────────────────────
  const handleSubmit = e => {
    e.preventDefault()

    // validate all 3 contacts
    const allErrors = contacts.map(validateContact)
    setContactErrors(allErrors)

    const hasErrors = allErrors.some(errs => Object.keys(errs).length > 0)
    if (hasErrors) return

    onSignup({
      name: name.trim(),
      email,
      password,
      emergency_contacts: contacts.map(c => ({
        name: c.name.trim(),
        phone: c.phone.trim(),
        relationship: c.relationship,
      })),
    })
  }

  // ── shared input class ─────────────────────────────────────────────────────
  const inputCls = hasErr =>
    `mt-1.5 w-full rounded-xl border px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 ${hasErr ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'
    }`

  // ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-emerald-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg rounded-3xl bg-white shadow-xl border border-emerald-100 p-8">

        {/* header */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-emerald-700">Join SakhiBot</h1>
          <p className="mt-1 text-sm text-gray-500">
            {step === 1 ? 'Create your secure account' : 'Add 3 emergency contacts'}
          </p>

          {/* step indicator */}
          <div className="flex items-center justify-center gap-2 mt-4">
            {[1, 2].map(s => (
              <div key={s} className="flex items-center gap-2">
                <div
                  className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors ${step >= s
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gray-100 text-gray-400'
                    }`}
                >
                  {s}
                </div>
                {s < 2 && (
                  <div
                    className={`h-1 w-10 rounded-full transition-colors ${step > s ? 'bg-emerald-500' : 'bg-gray-200'
                      }`}
                  />
                )}
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-gray-400">
            Step {step} of 2 — {step === 1 ? 'Account Details' : 'Emergency Contacts'}
          </p>
        </div>

        {/* ── STEP 1: Account details ───────────────────────────────────── */}
        {step === 1 && (
          <form onSubmit={handleNext} className="space-y-5">
            {(step1Error || error) && (
              <p className="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {step1Error || error}
              </p>
            )}

            <div>
              <label className="text-sm font-semibold text-gray-700">Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="e.g. Priya Sharma"
                className={inputCls(false)}
              />
            </div>

            <div>
              <label className="text-sm font-semibold text-gray-700">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className={inputCls(false)}
              />
            </div>

            <div>
              <label className="text-sm font-semibold text-gray-700">Password</label>
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                className={inputCls(false)}
              />
            </div>

            <button
              type="submit"
              className="w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-700 transition-colors"
            >
              Next →
            </button>

            <p className="text-center text-sm text-gray-500">
              Already have an account?{' '}
              <button type="button" onClick={onSwitch} className="text-emerald-600 font-semibold hover:underline">
                Login
              </button>
            </p>
          </form>
        )}

        {/* ── STEP 2: Emergency contacts ────────────────────────────────── */}
        {step === 2 && (
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <p className="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {error}
              </p>
            )}

            <p className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-xs text-amber-800 leading-5">
              🛡️ These contacts will be alerted in an emergency. Please double-check their phone numbers.
            </p>

            {contacts.map((contact, i) => {
              const errs = contactErrors[i]
              return (
                <div
                  key={i}
                  className="rounded-2xl border border-gray-100 bg-gray-50 p-4 space-y-3"
                >
                  <p className="text-xs font-bold uppercase tracking-wide text-emerald-700">
                    Contact {i + 1}
                  </p>

                  {/* Name */}
                  <div>
                    <label className="text-sm font-semibold text-gray-700">Name</label>
                    <input
                      type="text"
                      value={contact.name}
                      onChange={e => updateContact(i, 'name', e.target.value)}
                      placeholder="Letters and spaces only"
                      className={inputCls(!!errs.name)}
                    />
                    {errs.name && (
                      <p className="mt-1 text-xs text-red-600">{errs.name}</p>
                    )}
                  </div>

                  {/* Phone */}
                  <div>
                    <label className="text-sm font-semibold text-gray-700">Mobile Number</label>
                    <div className="relative mt-1.5">
                      <span className="absolute inset-y-0 left-3 flex items-center text-sm text-gray-500 pointer-events-none">
                        +91
                      </span>
                      <input
                        type="tel"
                        inputMode="numeric"
                        maxLength={10}
                        value={contact.phone}
                        onChange={e => {
                          const val = e.target.value.replace(/\D/g, '').slice(0, 10)
                          updateContact(i, 'phone', val)
                        }}
                        placeholder="10-digit number"
                        className={`w-full rounded-xl border px-4 py-3 pl-12 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 ${errs.phone ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-white'
                          }`}
                      />
                      {/* digit counter */}
                      <span
                        className={`absolute inset-y-0 right-3 flex items-center text-xs font-mono ${contact.phone.length === 10 ? 'text-emerald-600' : 'text-gray-400'
                          }`}
                      >
                        {contact.phone.length}/10
                      </span>
                    </div>
                    {errs.phone && (
                      <p className="mt-1 text-xs text-red-600">{errs.phone}</p>
                    )}
                  </div>

                  {/* Relationship dropdown */}
                  <div>
                    <label className="text-sm font-semibold text-gray-700">Relationship</label>
                    <select
                      value={contact.relationship}
                      onChange={e => updateContact(i, 'relationship', e.target.value)}
                      className={`mt-1.5 w-full rounded-xl border px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white ${errs.relationship ? 'border-red-400 bg-red-50' : 'border-gray-300'
                        }`}
                    >
                      <option value="">— Select relationship —</option>
                      {RELATIONSHIPS.map(r => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                    {errs.relationship && (
                      <p className="mt-1 text-xs text-red-600">{errs.relationship}</p>
                    )}
                  </div>
                </div>
              )
            })}

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="flex-1 rounded-xl border border-gray-300 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
              >
                ← Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 rounded-xl bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-wait disabled:bg-emerald-300 transition-colors"
              >
                {loading ? 'Creating account…' : 'Create Account'}
              </button>
            </div>

            <p className="text-center text-sm text-gray-500">
              Already have an account?{' '}
              <button type="button" onClick={onSwitch} className="text-emerald-600 font-semibold hover:underline">
                Login
              </button>
            </p>
          </form>
        )}

      </div>
    </div>
  )
}