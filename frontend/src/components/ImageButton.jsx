import { useRef } from 'react'

const MAX_IMAGE_BYTES = 8 * 1024 * 1024 // keep in sync with backend MAX_IMAGE_BYTES

export default function ImageButton({ onSelect, disabled }) {
  const inputRef = useRef(null)

  const handleChange = e => {
    const file = e.target.files?.[0]
    e.target.value = '' // allow selecting the same file again later

    if (!file) return

    if (!file.type.startsWith('image/')) {
      alert('Please choose an image file (JPG, PNG, etc.).')
      return
    }

    if (file.size > MAX_IMAGE_BYTES) {
      alert('That image is too large. Please choose one under 8MB.')
      return
    }

    onSelect(file)
  }

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleChange}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        title="Attach a photo or screenshot"
        className="w-10 h-10 rounded-full flex items-center justify-center
                   transition-all shrink-0 disabled:opacity-40
                   bg-emerald-50 text-emerald-600 hover:bg-emerald-100"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24"
          stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586
               a2 2 0 012.828 0L20 14M14 8h.01M6 20h12a2 2 0 002-2V6a2
               2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </button>
    </>
  )
}
