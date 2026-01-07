import { useState, useRef, useEffect } from 'react';
import { chatStream, getHistory } from './api/client';
import { Send, Bot, User, X, CheckCircle2, RefreshCw } from 'lucide-react';
import { VideoUpload } from './components/VideoUpload';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [videoId, setVideoId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string; type: 'success' | 'error' }>({ show: false, message: '', type: 'success' });
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast(prev => ({ ...prev, show: false })), 3000);
  };

  // Polling for progress updates
  useEffect(() => {
    let interval: any;
    if (videoId && !isStreaming) {
      interval = setInterval(async () => {
        try {
          const history = await getHistory(videoId);
          // Check if the new history is different (naive check length or last msg content)
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

  const handleUploadSuccess = (vid: string) => {
    setVideoId(vid);
    setLoading(true); // Simulate loading state/transition
    showToast("Video submitted! Processing started...", 'success');
    setMessages([]);
    setTimeout(() => setLoading(false), 500);
  };

  const handleUploadError = (err: string) => {
    showToast(err, 'error');
  };

  const handleSend = () => {
    if (!input.trim() || !videoId) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsStreaming(true);

    // Optimistic assistant message
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    chatStream(
      videoId,
      userMsg,
      (textChunk) => {
        setMessages(prev => {
          const newHistory = [...prev];
          // Create A COPY of the last message to modify it immutably
          const lastIndex = newHistory.length - 1;
          const lastMsg = { ...newHistory[lastIndex] };

          if (lastMsg.role === 'assistant') {
            lastMsg.content += textChunk;
            newHistory[lastIndex] = lastMsg;
          }
          return newHistory;
        });
      },
      () => setIsStreaming(false),
      (err) => {
        setIsStreaming(false);
        showToast("Chat error: " + err, 'error');
      }
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100 font-sans relative">
      {/* Toast Notification */}
      {toast.show && (
        <div className={`absolute top-4 left-1/2 transform -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2 rounded-full shadow-lg border animate-in fade-in slide-in-from-top-4 ${toast.type === 'success'
          ? 'bg-green-900/90 border-green-700 text-green-100'
          : 'bg-red-900/90 border-red-700 text-red-100'
          }`}>
          {toast.type === 'success' ? <CheckCircle2 size={16} /> : <X size={16} />}
          <span className="text-sm font-medium">{toast.message}</span>
        </div>
      )}

      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-950/50 backdrop-blur z-10">
        <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Obsidian AI
        </h1>
        {videoId && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => setVideoId(null)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-gray-800 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors border border-gray-700"
            >
              <RefreshCw size={16} />
              New Video
            </button>
          </div>
        )}
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-hidden relative flex flex-col">
        {!videoId ? (
          <div className="flex-1 flex items-center justify-center">
            <VideoUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>
        ) : (
          <div className="h-full flex flex-col">
            <div
              ref={scrollRef}
              className="flex-1 overflow-y-auto w-full max-w-3xl mx-auto p-4 space-y-6"
            >
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center shrink-0
                    ${msg.role === 'user' ? 'bg-blue-600' : 'bg-purple-600'}
                  `}>
                    {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </div>

                  <div className={`
                    max-w-[80%] rounded-2xl px-5 py-3 text-sm leading-relaxed
                    ${msg.role === 'user'
                      ? 'bg-blue-600 text-white rounded-tr-sm'
                      : 'bg-gray-800 border border-gray-700 text-gray-100 rounded-tl-sm shadow-sm'
                    }
                  `}>
                    {msg.content || (isStreaming && idx === messages.length - 1 ? <span className="animate-pulse">Thinking...</span> : '')}
                  </div>
                </div>
              ))}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-gray-800 bg-gray-900/95 backdrop-blur w-full max-w-3xl mx-auto">
              <div className="relative flex items-center">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                  placeholder="Ask something about the video..."
                  disabled={loading || isStreaming}
                  className="w-full bg-gray-800 text-gray-100 rounded-xl pl-4 pr-12 py-3.5 focus:outline-none focus:ring-2 focus:ring-blue-500/50 border border-gray-700 placeholder-gray-500 transition-all"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || loading || isStreaming}
                  className="absolute right-2 p-2 bg-blue-600 rounded-lg text-white hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
                >
                  <Send size={18} />
                </button>
              </div>
              <div className="text-center mt-2">
                <span className="text-xs text-gray-600 font-mono">
                  {loading ? 'Processing...' : isStreaming ? 'Generating response...' : 'Ready'}
                </span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
