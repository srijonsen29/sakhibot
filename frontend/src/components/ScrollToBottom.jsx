import { useState, useEffect } from 'react'

export default function ScrollToBottom({ containerRef }) {
  const [show, setShow] = useState(false)

  useEffect(() => {
    const el = containerRef?.current
    if (!el) return
    const onScroll = () => {
      const fromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
      setShow(fromBottom > 120)
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [containerRef])

  const scrollDown = () => {
    containerRef?.current?.scrollTo({ top: 999999, behavior: 'smooth' })
  }

  if (!show) return null

  return (
    <button
      onClick={scrollDown}
      className="absolute bottom-4 right-4 w-8 h-8 bg-white border
                 border-gray-200 rounded-full shadow-md flex items-center
                 justify-center text-gray-400 hover:text-emerald-600
                 hover:border-emerald-300 transition-colors z-10"
    >
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24"
        stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round"
          strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  )
}