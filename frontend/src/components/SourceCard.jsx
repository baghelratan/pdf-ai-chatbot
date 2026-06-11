import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

export default function SourceCard({ source, index }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="source-card" id={`source-card-${index}`}>
      <div
        className="source-card-header"
        onClick={() => setOpen(o => !o)}
        role="button"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && setOpen(o => !o)}
        aria-expanded={open}
      >
        <span className="source-badge">Src {index + 1}</span>
        <span className="source-file" title={source.filename}>
          📄 {source.filename}
        </span>
        <span className="source-page">Page {source.page_number}</span>
        <ChevronDown
          size={14}
          className={`source-expand ${open ? 'open' : ''}`}
        />
      </div>
      <div className={`source-excerpt ${open ? 'open' : ''}`}>
        "{source.text.slice(0, 400)}{source.text.length > 400 ? '…' : ''}"
      </div>
    </div>
  )
}
