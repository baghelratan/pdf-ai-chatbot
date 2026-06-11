import { useState, useRef, useCallback } from 'react'
import { Send } from 'lucide-react'
import UploadPanel from './components/UploadPanel.jsx'
import ChatWindow from './components/ChatWindow.jsx'

let msgCounter = 0
const newId = () => `msg-${++msgCounter}`

export default function App() {
  const [documents, setDocuments] = useState([])
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState(null)
  const textareaRef = useRef(null)

  const showError = (msg) => {
    setError(msg)
    setTimeout(() => setError(null), 5000)
  }

  const autoResize = () => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 150) + 'px'
  }

  const sendMessage = useCallback(async (text) => {
    const question = (text || input).trim()
    if (!question || streaming) return
    if (documents.length === 0) {
      showError('Please upload at least one PDF before asking questions.')
      return
    }

    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    // Add user message
    const userMsg = { id: newId(), role: 'user', content: question, timestamp: Date.now() }
    setMessages(prev => [...prev, userMsg])

    // Add placeholder assistant message
    const asstId = newId()
    setMessages(prev => [
      ...prev,
      { id: asstId, role: 'assistant', content: '', sources: [], timestamp: Date.now(), streaming: true },
    ])
    setStreaming(true)

    try {
      const body = {
        question,
        doc_ids: documents.map(d => d.doc_id),
        history: messages
          .slice(-12)
          .map(m => ({ role: m.role, content: m.content })),
      }

      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) throw new Error(`Server error ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') break

          let event
          try { event = JSON.parse(raw) } catch { continue }

          if (event.type === 'sources') {
            setMessages(prev =>
              prev.map(m =>
                m.id === asstId ? { ...m, sources: event.data } : m
              )
            )
          } else if (event.type === 'token') {
            accumulated += event.data
            const snapshot = accumulated
            setMessages(prev =>
              prev.map(m =>
                m.id === asstId ? { ...m, content: snapshot, streaming: true } : m
              )
            )
          } else if (event.type === 'error') {
            setMessages(prev =>
              prev.map(m =>
                m.id === asstId
                  ? { ...m, content: `⚠️ ${event.data}`, streaming: false }
                  : m
              )
            )
          }
        }
      }

      // Mark streaming done
      setMessages(prev =>
        prev.map(m =>
          m.id === asstId ? { ...m, streaming: false, timestamp: Date.now() } : m
        )
      )
    } catch (err) {
      showError(`Chat error: ${err.message}`)
      setMessages(prev => prev.filter(m => m.id !== asstId))
    } finally {
      setStreaming(false)
    }
  }, [input, streaming, documents, messages])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const docCount = documents.length

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-icon">🧠</div>
            <span className="logo-text">PDF Chatbot</span>
          </div>
          <div className="logo-tagline">Powered by Gemini AI</div>
        </div>

        <div style={{ padding: '16px 16px 0' }}>
          <UploadPanel
            documents={documents}
            onDocumentsChange={setDocuments}
          />
        </div>

        {docCount === 0 && (
          <div style={{ padding: '16px 20px', marginTop: 'auto' }}>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              📌 Upload a PDF to get started. Supports text-based and scanned documents.
            </p>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="main">
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-left">
            <h1>Chat with your PDFs</h1>
            <p>
              {docCount === 0
                ? 'No documents uploaded yet'
                : `${docCount} document${docCount > 1 ? 's' : ''} loaded — ask anything`}
            </p>
          </div>
          <div className="header-badge">
            <span className="dot" />
            Gemini 2.5 Flash
          </div>
        </header>

        {/* Messages */}
        <ChatWindow
          messages={messages}
          isStreaming={streaming}
          onSuggestion={(text) => sendMessage(text)}
        />

        {/* Input */}
        <div className="chat-input-area">
          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              className="chat-textarea"
              placeholder={
                docCount === 0
                  ? 'Upload a PDF first…'
                  : 'Ask anything about your documents…'
              }
              value={input}
              onChange={e => { setInput(e.target.value); autoResize() }}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={streaming}
              id="chat-input"
              aria-label="Chat input"
            />
            <button
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={!input.trim() || streaming || docCount === 0}
              id="send-btn"
              aria-label="Send message"
            >
              <Send size={16} />
            </button>
          </div>
          <div className="input-hints">
            <span className="input-hint">⏎ Send · Shift+⏎ New line</span>
            <span className="input-hint" style={{ color: 'var(--text-accent)' }}>
              {streaming ? '⚡ Generating…' : ''}
            </span>
          </div>
        </div>
      </main>

      {/* Error toast */}
      {error && (
        <div className="error-toast" role="alert" id="error-toast">
          ⚠️ {error}
        </div>
      )}
    </div>
  )
}
