import { useState } from 'react'

const STATES = [
  'Andhra Pradesh', 'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh',
  'Delhi', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Odisha',
  'Punjab', 'Rajasthan', 'Tamil Nadu', 'Telangana', 'Uttar Pradesh',
  'Uttarakhand', 'West Bengal',
]

export default function LocationPrompt({ onSubmit }) {
  const [district,  setDistrict]  = useState('')
  const [stateName, setStateName] = useState('')

  const handleSubmit = () => {
    if (!district.trim() || !stateName) return
    onSubmit(district.trim(), stateName)
  }

  return (
    <div className="mx-4 mb-3 bg-emerald-50 border border-emerald-200
                    rounded-2xl p-4">
      <p className="text-xs font-semibold text-emerald-800 mb-3 flex
                    items-center gap-1.5">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24"
          stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round"
            strokeWidth={2}
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827
               0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round"
            strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Where are you located?
      </p>

      <div className="space-y-2.5">
        <input
          type="text"
          placeholder="District (e.g. Mumbai, Kolkata, Jaipur)"
          value={district}
          onChange={e => setDistrict(e.target.value)}
          className="w-full text-sm border border-emerald-200 rounded-xl
                     px-3 py-2.5 bg-white focus:outline-none
                     focus:ring-2 focus:ring-emerald-300
                     placeholder-gray-400 text-gray-800"
        />

        <select
          value={stateName}
          onChange={e => setStateName(e.target.value)}
          className="w-full text-sm border border-emerald-200 rounded-xl
                     px-3 py-2.5 bg-white focus:outline-none
                     focus:ring-2 focus:ring-emerald-300 text-gray-800"
        >
          <option value="">Select state...</option>
          {STATES.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <button
          onClick={handleSubmit}
          disabled={!district.trim() || !stateName}
          className="w-full bg-emerald-600 hover:bg-emerald-700
                     disabled:bg-gray-200 disabled:text-gray-400
                     text-white text-sm font-medium rounded-xl
                     py-2.5 transition-colors"
        >
          Find resources near me
        </button>
      </div>
    </div>
  )
}