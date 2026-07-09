export default function ConnectionBanner({ onRetry }) {
  return (
    <div className="mx-4 my-2 bg-yellow-50 border border-yellow-200
                    rounded-xl px-4 py-3 flex items-center
                    justify-between gap-3">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-yellow-400 shrink-0" />
        <p className="text-xs text-yellow-800">
          Cannot reach server. Make sure the backend is running on
          port 8000.
        </p>
      </div>
      <button
        onClick={onRetry}
        className="text-xs text-yellow-700 font-medium
                   hover:underline shrink-0"
      >
        Retry
      </button>
    </div>
  )
}