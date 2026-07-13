import { useEffect, useState } from 'react'
import { getEmergencyContacts, updateEmergencyContacts } from '../../api'

const EMPTY_CONTACT = { name: '', phone: '', relationship: '' }

export default function EmergencyContactManager({ onClose, onSaved }) {
  const [contacts, setContacts] = useState([
    { ...EMPTY_CONTACT },
    { ...EMPTY_CONTACT },
    { ...EMPTY_CONTACT },
    { ...EMPTY_CONTACT },
    { ...EMPTY_CONTACT },
  ])
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [fetchLoading, setFetchLoading] = useState(true)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        // GET /api/auth/emergency-contacts returns a plain array
        const contactsArr = await getEmergencyContacts()
        const filled = [...Array(5)].map((_, i) =>
          contactsArr?.[i]
            ? {
                name: contactsArr[i].name || '',
                phone: contactsArr[i].phone || '',
                relationship: contactsArr[i].relationship || '',
              }
            : { ...EMPTY_CONTACT }
        )
        setContacts(filled)
      } catch {
        setLoadError('Could not load your existing contacts. You can still update below.')
      } finally {
        setFetchLoading(false)
      }
    }
    load()
  }, [])

  const handleFieldChange = (index, field, value) => {
    setContacts(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
    setSaved(false)
    setSaveError('')
  }

  const handleSave = async e => {
    e.preventDefault()
    setSaveError('')
    setSaving(true)

    const activeContacts = contacts.filter(
      c => c.name.trim() || c.phone.trim() || c.relationship.trim()
    )

    if (activeContacts.length < 3) {
      setSaveError('Please add at least 3 emergency contacts.')
      setSaving(false)
      return
    }

    for (let i = 0; i < activeContacts.length; i++) {
      const c = activeContacts[i]
      if (!c.name.trim() || !c.phone.trim() || !c.relationship.trim()) {
        setSaveError('Please fill in all fields for each contact you have started.')
        setSaving(false)
        return
      }
      if (!/^\+?[0-9]{7,15}$/.test(c.phone.trim())) {
        setSaveError(`Invalid phone for "${c.name || 'contact'}". Use 7-15 digits.`)
        setSaving(false)
        return
      }
    }

    const phones = activeContacts.map(c => c.phone.trim())
    if (new Set(phones).size !== phones.length) {
      setSaveError('Duplicate phone numbers are not allowed.')
      setSaving(false)
      return
    }

    try {
      await updateEmergencyContacts(activeContacts)
      setSaved(true)
      if (onSaved) onSaved()
    } catch (err) {
      setSaveError(
        err.response?.data?.detail || 'Failed to save contacts. Please try again.'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="ecm-title"
    >
      <div className="w-full max-w-2xl max-h-[92vh] overflow-y-auto rounded-3xl bg-white shadow-2xl">
        {/* header */}
        <div className="sticky top-0 bg-emerald-600 px-6 py-5 rounded-t-3xl flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-100">
              Account settings
            </p>
            <h2 id="ecm-title" className="mt-1 text-xl font-bold text-white">
              Manage Emergency Contacts
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close contact manager"
            className="rounded-full bg-white/15 px-3 py-1.5 text-sm font-semibold text-white hover:bg-white/25"
          >
            Close
          </button>
        </div>

        <div className="p-6">
          {/* WhatsApp share notice */}
          <div className="mb-5 rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            <span className="font-semibold">Tip:</span> In an SOS emergency, use the{' '}
            <strong>WhatsApp</strong> share button to instantly message these contacts your
            live location.
          </div>

          {fetchLoading ? (
            <div className="py-10 text-center text-sm text-gray-400">Loading your contacts…</div>
          ) : (
            <form onSubmit={handleSave} className="space-y-5">
              {loadError && (
                <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
                  {loadError}
                </p>
              )}

              {contacts.map((contact, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl border border-gray-100 bg-gray-50/60 p-4 space-y-3"
                >
                  <h3 className="text-sm font-semibold text-emerald-800">
                    Contact #{idx + 1}{' '}
                    <span className="font-normal text-gray-400">
                      {idx >= 3 ? '(Optional)' : '(Required)'}
                    </span>
                  </h3>
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                    {[
                      { field: 'name', label: 'Name', placeholder: 'Jane Doe', type: 'text' },
                      { field: 'phone', label: 'Mobile Number', placeholder: '9876543210', type: 'tel' },
                      { field: 'relationship', label: 'Relationship', placeholder: 'Sister / Friend', type: 'text' },
                    ].map(({ field, label, placeholder, type }) => (
                      <div key={field}>
                        <label className="text-xs font-medium text-gray-500">{label}</label>
                        <input
                          type={type}
                          value={contact[field]}
                          onChange={e => handleFieldChange(idx, field, e.target.value)}
                          placeholder={placeholder}
                          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm
                                     focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              {saveError && (
                <p className="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                  {saveError}
                </p>
              )}

              {saved && (
                <p className="rounded-xl bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
                  ✓ Contacts saved successfully.
                </p>
              )}

              <button
                type="submit"
                disabled={saving}
                className="w-full rounded-xl bg-emerald-600 py-3 font-semibold text-white
                           hover:bg-emerald-700 disabled:cursor-wait disabled:bg-emerald-300 transition-colors"
              >
                {saving ? 'Saving…' : 'Save Contacts'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
