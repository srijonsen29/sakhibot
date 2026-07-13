import { useState } from 'react'

export default function EmergencySetup({ onComplete }) {
  const [contacts, setContacts] = useState([
    { name: '', phone: '', relationship: '' },
    { name: '', phone: '', relationship: '' },
    { name: '', phone: '', relationship: '' },
    { name: '', phone: '', relationship: '' },
    { name: '', phone: '', relationship: '' },
  ])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleFieldChange = (index, field, value) => {
    setContacts(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
  }

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // filter out empty contacts
    const activeContacts = contacts.filter(
      c => c.name.trim() || c.phone.trim() || c.relationship.trim()
    )

    // validation checks
    if (activeContacts.length < 3) {
      setError('Please add at least 3 emergency contacts.')
      setLoading(false)
      return
    }

    // check complete records for active ones
    for (let i = 0; i < activeContacts.length; i++) {
      const c = activeContacts[i]
      if (!c.name.trim() || !c.phone.trim() || !c.relationship.trim()) {
        setError('Please fill in all fields (Name, Mobile, and Relationship) for each contact you have started.')
        setLoading(false)
        return
      }

      // Format validation (allows optional '+' prefix and 7-15 digits)
      if (!/^\+?[0-9]{7,15}$/.test(c.phone.trim())) {
        setError(`Invalid phone number format for ${c.name || 'contact'}. Numbers must contain between 7 to 15 digits.`)
        setLoading(false)
        return
      }
    }

    // check duplicates
    const phones = activeContacts.map(c => c.phone.trim())
    if (new Set(phones).size !== phones.length) {
      setError('Duplicate phone numbers are not allowed.')
      setLoading(false)
      return
    }

    try {
      await onComplete(activeContacts)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save emergency contacts. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-emerald-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-2xl rounded-3xl bg-white shadow-xl border border-emerald-100 p-8">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-emerald-700">Setup Emergency Contacts</h1>
          <p className="mt-2 text-gray-500">
            For your safety, please add emergency contacts. Min 3 required, max 5 allowed.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <p className="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
              {error}
            </p>
          )}

          <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
            {contacts.map((contact, idx) => (
              <div key={idx} className="p-4 rounded-2xl border border-gray-100 bg-gray-50/50 space-y-3">
                <h3 className="text-sm font-semibold text-emerald-800">
                  Contact #{idx + 1} {idx >= 3 ? '(Optional)' : '(Required)'}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs font-medium text-gray-500">Name</label>
                    <input
                      type="text"
                      value={contact.name}
                      onChange={e => handleFieldChange(idx, 'name', e.target.value)}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
                      placeholder="Jane Doe"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500">Mobile Number</label>
                    <input
                      type="tel"
                      value={contact.phone}
                      onChange={e => handleFieldChange(idx, 'phone', e.target.value)}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
                      placeholder="9876543210"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500">Relationship</label>
                    <input
                      type="text"
                      value={contact.relationship}
                      onChange={e => handleFieldChange(idx, 'relationship', e.target.value)}
                      className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
                      placeholder="Sister / Friend"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-wait disabled:bg-emerald-300"
          >
            {loading ? 'Saving Setup...' : 'Save and Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}
