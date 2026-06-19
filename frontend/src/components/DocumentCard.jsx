import { useState } from 'react'
import { downloadDocument } from '../api'

export default function DocumentCard({ documentType, history }) {
  const [loading, setLoading] = useState(false)
  const [downloaded, setDownloaded] = useState(false)

  if (!documentType) return null

  const LABELS = {
    fir:           'FIR Complaint Draft',
    dv_complaint:  'DV Act Complaint',
    posh_complaint:'POSH Complaint',
  }

  const label = LABELS[documentType] || 'Legal Document'

  const handleDownload = async () => {
    setLoading(true)
    try {
      const blob = await downloadDocument({ documentType, history })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `sakhibot_${documentType}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      setDownloaded(true)
    } catch (err) {
      console.error('Download failed:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mt-3 bg-white border border-emerald-200
                    rounded-xl p-3 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-emerald-100 rounded-lg flex items-center
                        justify-center shrink-0">
          <svg className="w-5 h-5 text-emerald-600" fill="none"
            viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0
                 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0
                 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-800">{label}</p>
          <p className="text-xs text-gray-500">Ready to print · PDF format</p>
        </div>

        <button
          onClick={handleDownload}
          disabled={loading}
          className={`shrink-0 flex items-center gap-1.5 text-xs font-medium
                     rounded-lg px-3 py-2 transition-colors
                     ${downloaded
                       ? 'bg-gray-100 text-gray-500'
                       : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                     } disabled:opacity-50`}
        >
          {loading ? (
            <svg className="w-3.5 h-3.5 animate-spin" fill="none"
              viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10"
                stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4
                   4m0 0l-4-4m4 4V4" />
            </svg>
          )}
          {loading ? 'Generating...' : downloaded ? 'Downloaded' : 'Download PDF'}
        </button>
      </div>
    </div>
  )
}