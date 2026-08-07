import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import ChatInput from './ChatInput'
import HITLBanner from './HITLBanner'
import './ChatWindow.css'

export default function ChatWindow({
  messages,
  isStreaming,
  streamingContent,
  currentTool,
  pendingInterrupt,
  onSendMessage,
  onUploadPdf,
  onApprove,
  onReject,
  disabled
}) {
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent, currentTool])

  const isEmpty = messages.length === 0 && !isStreaming

  return (
    <main className="chat-window">
      <div className="messages-area">
        {isEmpty ? (
          <div className="empty-state">
            <div className="empty-icon">✨</div>
            <h2>Ask me anything</h2>
            <p>I can help you with tasks, analyze documents, and use tools.</p>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((msg, index) => (
              <MessageBubble key={index} role={msg.role} content={msg.content} />
            ))}
            
            {isStreaming && streamingContent && (
              <MessageBubble role="assistant" content={streamingContent} isStreaming={true} />
            )}
            
            {currentTool && (
              <div className="tool-pill-container">
                <div className="tool-pill">
                  <span className="tool-icon">🔧</span>
                  Using {currentTool}...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="input-area">
        {pendingInterrupt && (
          <HITLBanner
            prompt={pendingInterrupt.prompt}
            onApprove={onApprove}
            onReject={onReject}
          />
        )}
        <ChatInput 
          onSend={onSendMessage} 
          onUploadPdf={onUploadPdf} 
          disabled={disabled} 
        />
      </div>
    </main>
  )
}
