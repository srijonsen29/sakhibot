export default function ResourceCard({ resources = [], helplines = [] }) {
  if (resources.length === 0 && helplines.length === 0) return null

  return (
    <div className="mt-3 space-y-2">
      {/* helplines strip */}
      {helplines.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {helplines.slice(0, 4).map((h, i) => (
            <a
              key={i}
              href={`tel:${h.phone}`}
              className="inline-flex items-center gap-1.5 bg-red-50
                         border border-red-200 text-red-700 text-xs
                         font-medium rounded-full px-3 py-1.5
                         hover:bg-red-100 transition-colors"
            >
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4
                         1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1
                         1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c.6 0 1 .4 1
                         1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"/>
              </svg>
              {h.phone} — {h.name}
            </a>
          ))}
        </div>
      )}

      {/* resource cards */}
      {resources.slice(0, 3).map((r, i) => (
        <div
          key={i}
          className="bg-white border border-gray-100 rounded-xl p-3
                     shadow-sm"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <TypeBadge type={r.type} />
                <span className="font-medium text-sm text-gray-800 truncate">
                  {r.name}
                </span>
              </div>
              {r.address && (
                <p className="text-xs text-gray-500 flex items-start gap-1">
                  <svg className="w-3 h-3 mt-0.5 shrink-0 text-emerald-500"
                    fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0
                         01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round"
                      strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  {r.address}
                </p>
              )}
              {r.open_hours && (
                <p className="text-xs text-gray-400 mt-0.5">
                  ⏰ {r.open_hours}
                </p>
              )}
            </div>

            {r.phone && (
              <a
                href={`tel:${r.phone}`}
                className="shrink-0 bg-emerald-600 hover:bg-emerald-700
                           text-white text-xs font-medium rounded-lg
                           px-3 py-1.5 transition-colors"
              >
                Call
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function TypeBadge({ type }) {
  const MAP = {
    osc:       { label: 'One Stop Centre', color: 'bg-emerald-100 text-emerald-700' },
    shelter:   { label: 'Shelter',         color: 'bg-blue-100 text-blue-700'      },
    legal_aid: { label: 'Legal Aid',       color: 'bg-purple-100 text-purple-700'  },
    helpline:  { label: 'Helpline',        color: 'bg-red-100 text-red-700'        },
  }
  const cfg = MAP[type] || { label: type, color: 'bg-gray-100 text-gray-600' }
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${cfg.color}`}>
      {cfg.label}
    </span>
  )
}
