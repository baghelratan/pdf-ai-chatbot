import { useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble.jsx'

const SUGGESTIONS = [
  '📋 Summarise this document',
  '🔍 What are the key findings?',
  '📌 List the main conclusions',
  '❓ What questions does this raise?',
]

export default function ChatWindow({ messages, isStreaming, onSuggestion }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="messages-container">
        <div className="welcome-state">
          <div className="welcome-icon">🧠</div>
          <h2 className="welcome-title">PDF AI Chatbot</h2>
          <p className="welcome-sub">
            Upload one or more PDF documents using the sidebar, then ask anything about their contents. I'll find the most relevant passages and cite the exact page numbers.
          </p>
          <div className="suggestion-chips">
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                className="chip"
                onClick={() => onSuggestion(s.replace(/^[^\s]+\s/, ''))}
                id={`suggestion-${i}`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="messages-container" id="messages-container">
      {messages.map(msg => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
