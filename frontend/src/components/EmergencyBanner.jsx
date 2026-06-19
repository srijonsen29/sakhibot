export default function EmergencyBanner({ onDismiss }) {
  return (
    <div className="mx-auto mb-3 w-[calc(100%-2rem)] max-w-3xl bg-red-50
                    border border-red-200 rounded-2xl p-4 shadow-sm sm:w-[calc(100%-3rem)]">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-red-100 rounded-full flex items-center
                          justify-center">
            <svg className="w-4 h-4 text-red-600" fill="none"
              viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667
                   1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464
                   0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <span className="font-semibold text-sm text-red-800">
            Emergency Help Available
          </span>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-red-400 hover:text-red-600 text-lg leading-none"
          >
            ×
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-2 mb-3 sm:grid-cols-2">
        {[
          { number: '181',        label: "Women's Helpline" },
          { number: '100',        label: 'Police' },
          { number: '112',        label: 'National Emergency' },
          { number: '7827170170', label: 'NCW Helpline' },
        ].map((h, i) => (
          <a
            key={i}
            href={`tel:${h.number}`}
            className="flex items-center gap-2 bg-white border
                       border-red-100 rounded-xl px-3 py-2.5
                       hover:bg-red-50 transition-colors group"
          >
            <div className="w-7 h-7 bg-red-100 rounded-full flex items-center
                            justify-center shrink-0
                            group-hover:bg-red-200 transition-colors">
              <svg className="w-3.5 h-3.5 text-red-600" fill="currentColor"
                viewBox="0 0 24 24">
                <path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3
                         .7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0
                         .6-.4 1-1 1-9.4 0-17-7.6-17-17 0-.6.4-1 1-1h3.5c.6
                         0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6
                         10.8z"/>
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-red-700">{h.number}</p>
              <p className="text-[10px] text-red-500 truncate">{h.label}</p>
            </div>
          </a>
        ))}
      </div>

      <p className="text-xs text-red-600 text-center">
        All helplines are free · Available 24 hours · You are not alone
      </p>
    </div>
  )
}
