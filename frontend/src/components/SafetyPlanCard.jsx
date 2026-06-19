import { useState } from 'react'

export default function SafetyPlanCard({ steps = [] }) {
  const [checked, setChecked] = useState({})

  if (!steps || steps.length === 0) return null

  const toggle = i =>
    setChecked(prev => ({ ...prev, [i]: !prev[i] }))

  const done = Object.values(checked).filter(Boolean).length

  return (
    <div className="mt-3 bg-amber-50 border border-amber-200
                    rounded-xl p-3">
      <div className="flex items-center justify-between mb-2.5">
        <span className="text-xs font-semibold text-amber-800
                         flex items-center gap-1.5">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24"
            stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0
                 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0
                 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          Your Safety Plan
        </span>
        <span className="text-xs text-amber-600 font-medium">
          {done}/{steps.length} done
        </span>
      </div>

      {/* progress bar */}
      <div className="w-full bg-amber-200 rounded-full h-1 mb-3">
        <div
          className="bg-amber-500 h-1 rounded-full transition-all duration-300"
          style={{ width: `${(done / steps.length) * 100}%` }}
        />
      </div>

      <div className="space-y-2">
        {steps.map((step, i) => (
          <button
            key={i}
            onClick={() => toggle(i)}
            className="w-full flex items-start gap-2.5 text-left
                       group"
          >
            <div className={`shrink-0 mt-0.5 w-5 h-5 rounded-full border-2
                            flex items-center justify-center transition-colors
                            ${checked[i]
                              ? 'bg-amber-500 border-amber-500'
                              : 'border-amber-400 group-hover:border-amber-500'
                            }`}>
              {checked[i] && (
                <svg className="w-3 h-3 text-white" fill="none"
                  viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round"
                    strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <span className={`text-xs text-amber-900 leading-relaxed
                               ${checked[i] ? 'line-through opacity-50' : ''}`}>
                <span className="font-semibold">Step {i + 1}.</span>{' '}
                {step}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}