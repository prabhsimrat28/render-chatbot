import './Sidebar.css'

export default function Sidebar({ threads, currentThreadId, onNewChat, onSelectThread, isOpen, onClose }) {
  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      <div className="sidebar-header">
        <span className="bot-icon">🤖</span>
        <h1>Agentic Chatbot</h1>
      </div>
      
      <button className="new-chat-btn" onClick={onNewChat}>
        <span className="plus-icon">+</span> New Chat
      </button>

      <div className="thread-list">
        {threads.map(id => (
          <button
            key={id}
            className={`thread-btn ${id === currentThreadId ? "active" : ""}`}
            onClick={() => onSelectThread(id)}
          >
            💬 {id.substring(0, 8)}...
          </button>
        ))}
      </div>
    </aside>
  )
}
