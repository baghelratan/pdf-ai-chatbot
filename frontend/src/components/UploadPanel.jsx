import { useState, useRef, useCallback } from 'react'
import { Upload, FileText, Trash2, ChevronDown } from 'lucide-react'

const MAX_MB = 50

export default function UploadPanel({ documents, onDocumentsChange }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressLabel, setProgressLabel] = useState('')
  const inputRef = useRef(null)

  const handleFiles = useCallback(async (files) => {
    const pdfs = [...files].filter(f => f.name.toLowerCase().endsWith('.pdf'))
    if (!pdfs.length) return

    // Size check
    for (const f of pdfs) {
      if (f.size > MAX_MB * 1024 * 1024) {
        alert(`"${f.name}" exceeds the ${MAX_MB} MB limit.`)
        return
      }
    }

    setUploading(true)
    setProgress(10)
    setProgressLabel(`Uploading ${pdfs.length} PDF(s)…`)

    const form = new FormData()
    pdfs.forEach(f => form.append('files', f))

    try {
      setProgress(40)
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      setProgress(80)

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Upload failed')
      }

      const data = await res.json()
      setProgress(100)
      setProgressLabel('Done!')
      onDocumentsChange(prev => [...prev, ...data.documents])
    } catch (err) {
      alert(`Upload error: ${err.message}`)
    } finally {
      setTimeout(() => {
        setUploading(false)
        setProgress(0)
        setProgressLabel('')
      }, 800)
    }
  }, [onDocumentsChange])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  const onDragOver = useCallback((e) => { e.preventDefault(); setDragging(true) }, [])
  const onDragLeave = useCallback(() => setDragging(false), [])

  const handleDelete = async (docId) => {
    if (!confirm('Remove this document?')) return
    try {
      await fetch(`/api/documents/${docId}`, { method: 'DELETE' })
      onDocumentsChange(prev => prev.filter(d => d.doc_id !== docId))
    } catch {
      alert('Failed to remove document.')
    }
  }

  return (
    <>
      {/* Drop zone */}
      <div
        className={`upload-zone ${dragging ? 'drag-over' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        id="upload-zone"
        role="button"
        aria-label="Upload PDF files"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
      >
        <span className="upload-icon">📄</span>
        <div className="upload-title">Drop PDFs here</div>
        <div className="upload-sub">or click to browse<br/>Up to {MAX_MB} MB per file</div>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          className="upload-input"
          onChange={e => handleFiles(e.target.files)}
          id="pdf-file-input"
        />
      </div>

      {/* Upload progress */}
      {uploading && (
        <div className="upload-progress">
          <div className="progress-label">
            <span>{progressLabel}</span>
            <span>{progress}%</span>
          </div>
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {/* Document list */}
      {documents.length > 0 && (
        <>
          <div className="sidebar-section">Documents ({documents.length})</div>
          <div className="doc-list">
            {documents.map(doc => (
              <div key={doc.doc_id} className="doc-item" id={`doc-${doc.doc_id}`}>
                <div className="doc-icon">📑</div>
                <div className="doc-info">
                  <div className="doc-name" title={doc.filename}>{doc.filename}</div>
                  <div className="doc-meta">{doc.page_count} pages · {doc.chunk_count} chunks</div>
                </div>
                <button
                  className="doc-delete"
                  onClick={(e) => { e.stopPropagation(); handleDelete(doc.doc_id) }}
                  title="Remove document"
                  aria-label={`Remove ${doc.filename}`}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  )
}
