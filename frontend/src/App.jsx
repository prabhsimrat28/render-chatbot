import { useState } from 'react'
import { useChat } from './hooks/useChat'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import './App.css'

function App() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const {
    threads,
    currentThreadId,
    messages,
    isStreaming,
    currentTool,
    pendingInterrupt,
    streamingContent,
    sendMessage,
    createNewThread,
    switchThread,
    uploadPdf,
    resumeHitl
  } = useChat()

  return (
    <div className="app">
      <button 
        className="mobile-toggle" 
        onClick={() => setMobileOpen(true)}
        aria-label="Open sidebar"
      >
        ☰
      </button>

      {mobileOpen && (
        <div 
          className="sidebar-overlay active"
          onClick={() => setMobileOpen(false)}
        ></div>
      )}

      <Sidebar 
        threads={threads}
        currentThreadId={currentThreadId}
        onNewChat={() => {
          createNewThread();
          setMobileOpen(false);
        }}
        onSelectThread={(id) => {
          switchThread(id);
          setMobileOpen(false);
        }}
        isOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      <ChatWindow 
        messages={messages}
        isStreaming={isStreaming}
        streamingContent={streamingContent}
        currentTool={currentTool}
        pendingInterrupt={pendingInterrupt}
        onSendMessage={sendMessage}
        onUploadPdf={uploadPdf}
        onApprove={() => resumeHitl('yes')}
        onReject={() => resumeHitl('no')}
        disabled={isStreaming || pendingInterrupt !== null}
      />
    </div>
  )
}

export default App
