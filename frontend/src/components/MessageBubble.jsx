import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './MessageBubble.css'

export default function MessageBubble({ role, content, isStreaming }) {
  const isUser = role === 'user'

  return (
    <div className={`message-row ${isUser ? 'user-row' : 'assistant-row'}`}>
      {!isUser && (
        <div className="bot-avatar">🤖</div>
      )}
      <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
        {isUser ? (
          <div className="message-content text-content">{content}</div>
        ) : (
          <div className="message-content markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
            {isStreaming && <span className="cursor-blink">▊</span>}
          </div>
        )}
      </div>
    </div>
  )
}
