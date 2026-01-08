import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { MainLayout } from './layouts/MainLayout';
import { getHistory, listSessions, createSession, getStatus } from './api/client';
import { Sparkles } from 'lucide-react';
import { getCurrentWindow } from '@tauri-apps/api/window';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [isInitializing, setIsInitializing] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessions, setSessions] = useState<any[]>([]);

  // Toast State
  const [toast, setToast] = useState<{ show: boolean; msg: string; type: 'success' | 'error' }>({ show: false, msg: '', type: 'success' });

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ show: true, msg, type });
    setTimeout(() => setToast(prev => ({ ...prev, show: false })), 3000);
  };

  const refreshSessions = async () => {
    console.log("Refreshing sessions list...");
    try {
      const sess = await listSessions();
      console.log("Sessions fetched:", sess);
      setSessions(sess);
    } catch (e: any) {
      console.error("Failed to fetch sessions", e);
      showToast("Failed to refresh history: " + e.message || e, 'error');
    }
  };

  // Initial Data Fetch & Model Status Polling
  useEffect(() => {
    console.log("Attempting to show window...");
    try {
      getCurrentWindow().show();
      console.log("Window show command sent.");
    } catch (e) {
      console.error("Failed to show window:", e);
    }

    const init = async () => {
      // 1. Refresh Sessions
      await refreshSessions();

      // 2. Poll for Model Status
      console.log("Polling for model status...");
      let ready = false;
      let retries = 0;
      while (!ready) {
        ready = await getStatus();
        if (!ready) {
          // Basic backoff or just constant poll
          await new Promise(r => setTimeout(r, 1000));
          retries++;
          if (retries % 5 === 0) console.log("Still loading model...");
        }
      }
      console.log("Model loaded!");

      setTimeout(() => setIsInitializing(false), 500);
    };

    init();
  }, []);

  // Polling for chat history
  useEffect(() => {
    let interval: any;
    if (sessionId && !isStreaming) {
      interval = setInterval(async () => {
        try {
          const history = await getHistory(sessionId);
          setMessages(prev => {
            if (JSON.stringify(prev) !== JSON.stringify(history)) {
              return history;
            }
            return prev;
          });
        } catch (e) {
          // Silent fail for polling
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [sessionId, isStreaming]);

  const handleNewChat = async () => {
    setIsStreaming(false);
    try {
      const newId = await createSession(null);
      setSessionId(newId);
      setMessages([]);
      refreshSessions();
    } catch (e: any) {
      showToast("Failed to create new chat: " + e.message, 'error');
    }
  };

  const handleUploadSuccess = async (vidId: string) => {
    // Create a session for this video
    try {
      const newId = await createSession(vidId);
      setSessionId(newId);
      setMessages([]);
      refreshSessions();
      showToast("Video submitted! Processing started...", 'success');
    } catch (e: any) {
      showToast("Failed to create session for video: " + e.message, 'error');
    }
  };

  const handleSelectSession = (id: string) => {
    setSessionId(id);
    setMessages([]); // Will update on next poll or immediate fetch
    getHistory(id).then(setMessages).catch(console.error);
  };

  if (isInitializing) {
    return (
      <div className="h-screen w-screen bg-gray-950 flex flex-col items-center justify-center space-y-4">
        <div className="relative">
          <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 animate-pulse rounded-full"></div>
          <Sparkles size={48} className="text-blue-400 animate-pulse drop-shadow-[0_0_15px_rgba(96,165,250,0.8)] relative z-10" />
        </div>
        <div className="text-gray-400 font-medium animate-pulse">
          Loading AI Model... (this may take a minute)
        </div>
      </div>
    );
  }

  return (
    <MainLayout
      sidebar={
        <Sidebar
          isOpen={isSidebarOpen}
          setIsOpen={setIsSidebarOpen}
          onNewChat={handleNewChat}
          onSelectSession={handleSelectSession}
          sessions={sessions}
          activeSessionId={sessionId}
          onRefreshSessions={refreshSessions}
        />
      }
    >
      <ChatArea
        sessionId={sessionId}
        onUploadSuccess={handleUploadSuccess}
        onUploadError={(err) => showToast(err, 'error')}
        messages={messages}
        setMessages={setMessages}
        isStreaming={isStreaming}
        setIsStreaming={setIsStreaming}
        onToast={showToast}
        refreshSessions={refreshSessions}
        onSessionChange={(id) => setSessionId(id)}
      />

      {/* Global Toast Overlay */}
      {toast.show && (
        <div className={`
          absolute top-4 left-1/2 transform -translate-x-1/2 z-50 
          flex items-center gap-2 px-4 py-2 rounded-full shadow-lg border 
          animate-in fade-in slide-in-from-top-4 
          ${toast.type === 'success' ? 'bg-green-900/90 border-green-700 text-green-100' : 'bg-red-900/90 border-red-700 text-red-100'}
        `}>
          <span className="text-sm font-medium">{toast.msg}</span>
        </div>
      )}
    </MainLayout>
  );
}

export default App;
