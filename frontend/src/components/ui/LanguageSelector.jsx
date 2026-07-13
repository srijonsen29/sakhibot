const LANGUAGES = [
  { code: 'en', name: 'English',   native: 'English'   },
  { code: 'hi', name: 'Hindi',     native: 'हिंदी'      },
  { code: 'bn', name: 'Bengali',   native: 'বাংলা'      },
  { code: 'ta', name: 'Tamil',     native: 'தமிழ்'      },
  { code: 'te', name: 'Telugu',    native: 'తెలుగు'     },
  { code: 'mr', name: 'Marathi',   native: 'मराठी'      },
  { code: 'gu', name: 'Gujarati',  native: 'ગુજરાતી'   },
  { code: 'kn', name: 'Kannada',   native: 'ಕನ್ನಡ'      },
  { code: 'ml', name: 'Malayalam', native: 'മലയാളം'    },
]

export default function LanguageSelector({ value, onChange }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="appearance-none bg-emerald-50 text-emerald-800 border
                   border-emerald-300 text-xs font-medium rounded-full
                   pl-3 pr-7 py-1.5 cursor-pointer focus:outline-none
                   focus:ring-2 focus:ring-emerald-400"
      >
        {LANGUAGES.map(lang => (
          <option key={lang.code} value={lang.code}>
            {lang.native}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute right-2 top-1/2
                      -translate-y-1/2 text-emerald-600">
        <svg width="10" height="6" viewBox="0 0 10 6" fill="currentColor">
          <path d="M0 0l5 6 5-6H0z" />
        </svg>
      </div>
    </div>
  )
}