import { useState, useEffect } from 'react';
import * as apiClient from '../api/client';

export function useChat() {
  const [threads, setThreads] = useState([]);
  const [currentThreadId, setCurrentThreadId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentTool, setCurrentTool] = useState(null);
  const [pendingInterrupt, setPendingInterrupt] = useState(null);
  const [streamingContent, setStreamingContent] = useState('');

  useEffect(() => {
    loadInitialData();
  }, []);

  async function loadInitialData() {
    try {
      const threadList = await apiClient.fetchThreads();
      if (threadList.length === 0) {
        await createNewThread();
      } else {
        setThreads(threadList);
        await switchThread(threadList[0]);
      }
    } catch (error) {
    }
  }

  async function createNewThread() {
    try {
      const id = await apiClient.createThread();
      setThreads(prev => [id, ...prev]);
      setCurrentThreadId(id);
      setMessages([]);
      setPendingInterrupt(null);
      return id;
    } catch (error) {
    }
  }

  async function switchThread(id) {
    try {
      setCurrentThreadId(id);
      const msgs = await apiClient.fetchMessages(id);
      setMessages(msgs);
      const interrupt = await apiClient.checkInterrupt(id);
      setPendingInterrupt(interrupt.pending ? { prompt: interrupt.prompt } : null);
    } catch (error) {
    }
  }

  async function sendMessage(text) {
    if (isStreaming || !currentThreadId) return;
    
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setIsStreaming(true);
    setStreamingContent('');
    setCurrentTool(null);
    setPendingInterrupt(null);
    
    let contentAccumulator = '';
    
    await apiClient.streamChat(currentThreadId, text, {
      onToken: (token) => {
        contentAccumulator += token;
        setStreamingContent(contentAccumulator);
        setCurrentTool(null);
      },
      onToolUse: (tool) => {
        setCurrentTool(tool);
      },
      onInterrupt: (data) => {
        setPendingInterrupt({ prompt: data.prompt });
        setIsStreaming(false);
      },
      onDone: () => {
        if (contentAccumulator) {
          setMessages(prev => [...prev, { role: 'assistant', content: contentAccumulator }]);
        }
        setIsStreaming(false);
        setStreamingContent('');
        setCurrentTool(null);
      },
      onError: (err) => {
        setIsStreaming(false);
        setCurrentTool(null);
      }
    });
  }

  async function resumeHitl(decision) {
    if (!currentThreadId) return;
    
    setPendingInterrupt(null);
    setIsStreaming(true);
    setStreamingContent('');
    setCurrentTool(null);
    
    let contentAccumulator = '';
    
    await apiClient.streamResume(currentThreadId, decision, {
      onToken: (token) => {
        contentAccumulator += token;
        setStreamingContent(contentAccumulator);
        setCurrentTool(null);
      },
      onToolUse: (tool) => {
        setCurrentTool(tool);
      },
      onInterrupt: (data) => {
        setPendingInterrupt({ prompt: data.prompt });
        setIsStreaming(false);
      },
      onDone: () => {
        if (contentAccumulator) {
          setMessages(prev => [...prev, { role: 'assistant', content: contentAccumulator }]);
        }
        setIsStreaming(false);
        setStreamingContent('');
        setCurrentTool(null);
      },
      onError: (err) => {
        setIsStreaming(false);
        setCurrentTool(null);
      }
    });
  }

  async function uploadPdf(file) {
    return await apiClient.uploadPdf(file);
  }

  return {
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
  };
}
