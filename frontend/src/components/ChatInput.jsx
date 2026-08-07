import { useState, useRef } from 'react'
import './ChatInput.css'

export default function ChatInput({ onSend, onUploadPdf, disabled }) {
  const [text, setText] = useState('')
  const [toastMessage, setToastMessage] = useState(null)
  const fileInputRef = useRef(null)

  const handleSend = () => {
    if (text.trim() && !disabled) {
      onSend(text.trim())
      setText('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    if (file.type !== 'application/pdf') {
      showToast('Only PDF files are supported')
      return
    }

    try {
      const res = await onUploadPdf(file)
      showToast(`Uploaded: ${res.filename}`)
    } catch (error) {
      showToast('Failed to upload PDF')
    }
    
    e.target.value = null
  }

  const showToast = (msg) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 3000)
  }

  return (
    <div className="chat-input-wrapper">
      {toastMessage && (
        <div className="toast-notification">
          {toastMessage}
        </div>
      )}
      
      <div className={`chat-input-container ${disabled ? 'disabled' : ''}`}>
        <button 
          className="icon-btn paperclip-btn" 
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Upload PDF"
        >
          📎
        </button>
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          accept="application/pdf"
          onChange={handleFileChange}
        />
        
        <textarea
          className="text-input"
          placeholder={disabled ? "Waiting..." : "Type a message..."}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          style={{
            height: 'auto',
            minHeight: '24px'
          }}
        />
        
        <button 
          className="send-btn" 
          onClick={handleSend}
          disabled={!text.trim() || disabled}
        >
          ➤
        </button>
      </div>
    </div>
  )
}
