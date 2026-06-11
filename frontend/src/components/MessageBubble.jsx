import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import SourceCard from './SourceCard.jsx'

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function MessageBubble({ message }) {
  const { role, content, sources, timestamp, streaming } = message
  const isUser = role === 'user'

  return (
    <div className={`message ${role}`} id={`msg-${message.id}`}>
      <div className="message-avatar">
        {isUser ? '👤' : '🤖'}
      </div>
      <div className="message-body">
        <div className="message-bubble">
          {content ? (
            isUser ? (
              <span>{content}</span>
            ) : (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            )
          ) : (
            /* Typing indicator while streaming starts */
            <div className="typing-indicator">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          )}
        </div>

        {/* Source attribution */}
        {!isUser && sources && sources.length > 0 && !streaming && (
          <div className="sources-section">
            <div className="sources-label">
              {sources.length} source{sources.length > 1 ? 's' : ''} referenced
            </div>
            <div className="source-cards">
              {sources.map((src, i) => (
                <SourceCard key={i} source={src} index={i} />
              ))}
            </div>
          </div>
        )}

        <div className="message-time">{formatTime(timestamp)}</div>
      </div>
    </div>
  )
}
