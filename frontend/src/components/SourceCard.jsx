export default function SourceCard({ sources = [] }) {
  if (!sources || sources.length === 0) return null

  // deduplicate by source name
  const unique = sources.filter(
    (s, i, arr) => arr.findIndex(x => x.source === s.source) === i
  )

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {unique.slice(0, 4).map((s, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 text-xs bg-white
                     border border-gray-200 text-gray-500 rounded-lg
                     px-2 py-1"
        >
          <svg
            className="w-3 h-3 text-emerald-500 shrink-0"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586
                 a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19
                 a2 2 0 01-2 2z" />
          </svg>
          {s.source}
        </span>
      ))}
    </div>
  )
}