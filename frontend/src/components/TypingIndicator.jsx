export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 px-4">
      <div className="w-7 h-7 rounded-full bg-emerald-100 flex items-center
                      justify-center text-emerald-700 text-xs font-bold
                      shrink-0 mt-0.5 select-none">
        S
      </div>
      <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3
                      flex items-center gap-1.5">
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  )
}