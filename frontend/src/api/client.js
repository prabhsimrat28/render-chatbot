export async function processSSEStream(response, callbacks) {
  const { onToken, onToolUse, onInterrupt, onDone, onError } = callbacks;
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let currentEvent = 'message';

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          currentEvent = 'message';
          continue;
        }

        if (trimmed.startsWith('event: ')) {
          currentEvent = trimmed.slice(7).trim();
        } else if (trimmed.startsWith('data: ')) {
          const dataStr = trimmed.slice(6);
          if (dataStr === '[DONE]') {
            if (onDone) onDone();
            continue;
          }
          
          try {
            const data = JSON.parse(dataStr);
            if (currentEvent === 'token' && onToken) {
              onToken(data.content);
            } else if (currentEvent === 'tool_use' && onToolUse) {
              onToolUse(data.tool);
            } else if (currentEvent === 'interrupt' && onInterrupt) {
              onInterrupt(data);
            } else if (currentEvent === 'done' && onDone) {
              onDone();
            } else if (currentEvent === 'error' && onError) {
              onError(data.error);
            }
          } catch (e) {
          }
        }
      }
    }
  } catch (error) {
    if (onError) onError(error.message);
  } finally {
    reader.releaseLock();
  }
}

export async function fetchThreads() {
  const res = await fetch('/api/threads');
  const data = await res.json();
  return data.threads;
}

export async function createThread() {
  const res = await fetch('/api/threads', { method: 'POST' });
  const data = await res.json();
  return data.thread_id;
}

export async function fetchMessages(threadId) {
  const res = await fetch(`/api/threads/${threadId}/messages`);
  const data = await res.json();
  return data.messages;
}

export async function checkInterrupt(threadId) {
  const res = await fetch(`/api/threads/${threadId}/interrupt`);
  return await res.json();
}

export async function streamChat(threadId, message, callbacks) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ thread_id: threadId, message })
  });
  await processSSEStream(res, callbacks);
}

export async function streamResume(threadId, decision, callbacks) {
  const res = await fetch('/api/chat/resume', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ thread_id: threadId, decision })
  });
  await processSSEStream(res, callbacks);
}

export async function uploadPdf(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/upload-pdf', {
    method: 'POST',
    body: formData
  });
  return await res.json();
}
