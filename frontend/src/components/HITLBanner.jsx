import './HITLBanner.css'

export default function HITLBanner({ prompt, onApprove, onReject }) {
  return (
    <div className="hitl-banner">
      <div className="hitl-header">
        <span className="hitl-icon">⚠️</span>
        <h3 className="hitl-title">Human Approval Required</h3>
      </div>
      <p className="hitl-prompt">{prompt}</p>
      <div className="hitl-actions">
        <button className="hitl-btn hitl-approve" onClick={onApprove}>
          ✅ Approve
        </button>
        <button className="hitl-btn hitl-reject" onClick={onReject}>
          ❌ Reject
        </button>
      </div>
    </div>
  )
}
