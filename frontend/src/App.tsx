import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { MainLayout } from './layouts/MainLayout';
import { getHistory } from './api/client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  // Toast State (Simple local implementation for now, could be Context)
  const [toast, setToast] = useState<{ show: boolean; msg: string; type: 'success' | 'error' }>({ show: false, msg: '', type: 'success' });

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ show: true, msg, type });
    setTimeout(() => setToast(prev => ({ ...prev, show: false })), 3000);
  };

  // Polling for progress (Keep this logic central for now)
  useEffect(() => {
    let interval: any;
    if (videoId && !isStreaming) {
      interval = setInterval(async () => {
        try {
          const history = await getHistory(videoId);
          setMessages(prev => {
            const lastOld = prev[prev.length - 1];
            const lastNew = history[history.length - 1];
            if (!lastOld || !lastNew || lastOld.content !== lastNew.content || prev.length !== history.length) {
              return history;
            }
            return prev;
          });
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [videoId, isStreaming]);

  const handleNewChat = () => {
    setVideoId(null);
    setMessages([]);
    setIsStreaming(false);
  };

  const handleUploadSuccess = (vid: string) => {
    setVideoId(vid);
    setMessages([]);
    showToast("Video submitted! Processing started...", 'success');
  };

  return (
    <MainLayout
      sidebar={
        <Sidebar
          isOpen={isSidebarOpen}
          setIsOpen={setIsSidebarOpen}
          onNewChat={handleNewChat}
        />
      }
    >
      <ChatArea
        videoId={videoId}
        onUploadSuccess={handleUploadSuccess}
        onUploadError={(err) => showToast(err, 'error')}
        messages={messages}
        setMessages={setMessages}
        isStreaming={isStreaming}
        setIsStreaming={setIsStreaming}
        onToast={showToast}
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
