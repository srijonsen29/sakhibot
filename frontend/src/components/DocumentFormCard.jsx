import { useState } from 'react'
import { submitDocumentForm } from '../api'

const INPUT_TYPE_MAP = {
  text: 'text',
  number: 'number',
  tel: 'tel',
  date: 'date',
  time: 'time',
}

export default function DocumentFormCard({ form, language = 'en', onSubmitted }) {
  const [values, setValues] = useState(() =>
    Object.fromEntries(form.fields.map(f => [f.name, f.value || '']))
  )
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [done, setDone] = useState(false)

  function handleChange(name, value) {
    setValues(prev => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors(prev => {
        const next = { ...prev }
        delete next[name]
        return next
      })
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitError('')

    const missing = form.fields.filter(f => f.required && !values[f.name]?.trim())
    if (missing.length > 0) {
      setErrors(Object.fromEntries(missing.map(f => [f.name, true])))
      setSubmitError('Please fill in all required fields before submitting.')
      return
    }

    setSubmitting(true)
    try {
      const blob = await submitDocumentForm({
        documentType: form.doc_type,
        fields: values,
        language,
      })

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sakhibot_${form.doc_type}_${language}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)

      setDone(true)
      onSubmitted?.()
    } catch (err) {
      console.error('Document form submit failed:', err)

      if (err.response?.status === 422) {
        const verdict = err.response.data?.verdict
        const fieldErrors = Object.fromEntries(
          (verdict?.missing_fields || verdict?.untraceable_fields || [])
            .map(name => [name, true])
        )
        setErrors(fieldErrors)
        setSubmitError(
          verdict?.warnings?.[0] ||
          'Some details look incomplete or invalid. Please review the highlighted fields.'
        )
        return
      }

      if (err.response?.status === 401) {
        setSubmitError('Your session has expired. Please log in again.')
        return
      }

      setSubmitError('Could not generate the document. Please check your connection and try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-800">
        Your document has been generated and downloaded. Please review it carefully
        before submitting it to the relevant authority.
      </div>
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm"
    >
      <div>
        <h3 className="text-sm font-bold text-gray-900">{form.title}</h3>
        <p className="mt-1 text-xs leading-5 text-gray-500">
          Please fill in the details below — you can review and edit anything before submitting.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {form.fields.map(field => (
          <div key={field.name} className={field.type === 'textarea' ? 'sm:col-span-2' : ''}>
            <label className="mb-1 block text-xs font-semibold text-gray-700">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>

            {field.type === 'textarea' ? (
              <textarea
                rows={3}
                value={values[field.name]}
                placeholder={field.placeholder}
                onChange={e => handleChange(field.name, e.target.value)}
                className={`w-full rounded-xl border px-3 py-2 text-sm text-gray-900
                           focus:outline-none focus:ring-2 focus:ring-emerald-300
                           ${errors[field.name] ? 'border-red-400' : 'border-gray-200'}`}
              />
            ) : (
              <input
                type={INPUT_TYPE_MAP[field.type] || 'text'}
                value={values[field.name]}
                placeholder={field.placeholder}
                onChange={e => handleChange(field.name, e.target.value)}
                className={`w-full rounded-xl border px-3 py-2 text-sm text-gray-900
                           focus:outline-none focus:ring-2 focus:ring-emerald-300
                           ${errors[field.name] ? 'border-red-400' : 'border-gray-200'}`}
              />
            )}

            {errors[field.name] && (
              <p className="mt-1 text-[11px] font-semibold text-red-500">This field is required</p>
            )}
          </div>
        ))}
      </div>

      {submitError && (
        <p className="rounded-xl bg-red-50 px-3 py-2 text-xs font-medium text-red-700">
          {submitError}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-bold text-white
                   hover:bg-emerald-700 disabled:cursor-wait disabled:opacity-60"
      >
        {submitting ? 'Generating document...' : 'Generate document'}
      </button>
    </form>
  )
}
