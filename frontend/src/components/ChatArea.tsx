import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Video, Plus, Image as ImageIcon, AudioLines } from 'lucide-react';
import { chatStream, uploadVideo } from '../api/client';
import { open } from '@tauri-apps/plugin-dialog';
import { invoke } from '@tauri-apps/api/core';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

interface ChatAreaProps {
    videoId: string | null;
    onUploadSuccess: (vid: string) => void;
    onUploadError: (err: string) => void;
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    isStreaming: boolean;
    setIsStreaming: (streaming: boolean) => void;
    onToast: (msg: string, type: 'success' | 'error') => void;
}

export function ChatArea({
    videoId,
    onUploadSuccess,
    onUploadError,
    messages,
    setMessages,
    isStreaming,
    setIsStreaming,
    onToast
}: ChatAreaProps) {
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false); // Local loading for upload
    const [username, setUsername] = useState('there');
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isStreaming]);

    // Fetch Username
    useEffect(() => {
        invoke('get_username')
            .then((name) => setUsername(name as string))
            .catch(console.error);
    }, []);

    // Upload Logic (Refactored from VideoUpload)
    const handleUpload = async () => {
        try {
            const selected = await open({
                multiple: false,
                filters: [{
                    name: 'Video',
                    extensions: ['mp4', 'mkv', 'avi', 'mov']
                }]
            });

            if (selected && typeof selected === 'string') {
                const path = selected;
                setLoading(true);
                try {
                    const vid = await uploadVideo(path);
                    onUploadSuccess(vid);
                } catch (err: any) {
                    console.error(err);
                    onUploadError(err.toString());
                } finally {
                    setLoading(false);
                }
            }
        } catch (err: any) {
            console.error(err);
            onToast("File selection failed: " + err.toString(), 'error');
        }
    };

    const handleSend = (text: string = input) => {
        const msgText = text.trim();
        if (!msgText) return;

        if (!videoId) {
            // Handle "Chatting without video"
            // For now, we just prompt them to upload if they try to ask specific questions
            // Or we can treat "Analyze" keywords as triggers
            if (msgText.toLowerCase().includes('analyze') || msgText.toLowerCase().includes('upload')) {
                handleUpload();
                return;
            }

            // General echo for now
            setMessages(prev => [...prev, { role: 'user', content: msgText }]);
            setMessages(prev => [...prev, { role: 'assistant', content: "Please upload a video first so I can help you analyze it! Click the + button or use the shortcuts above." }]);
            setInput('');
            return;
        }

        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: msgText }]);
        setIsStreaming(true);

        // Optimistic assistant message
        setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

        chatStream(
            videoId,
            msgText,
            (textChunk) => {
                setMessages(prev => {
                    const newHistory = [...prev];
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
                onToast("Chat error: " + err, 'error');
            }
        );
    };

    // Shortcut Chips
    const shortcuts = [
        { icon: <Video size={16} />, text: "Analyze a video", action: handleUpload },
        // TODO: Re-enable these when we have backend support
        // { icon: <MessageSquare size={16} />, text: "Summarize typical content", action: () => handleSend("What usually happens in these videos?") }, 
        // { icon: <FileQuestion size={16} />, text: "Help me learn", action: () => handleSend("How does this tool work?") },
    ];

    // Helper to determine if we show the "Welcome" state
    const showWelcome = !videoId && messages.length === 0;

    return (
        <div className="flex flex-col h-full relative">
            {/* Messages Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto px-4 py-6 space-y-6"
            >
                {showWelcome ? (
                    /* Empty State for Chat - Gemini Style */
                    <div className="h-full flex flex-col items-center justify-center space-y-8 duration-700 delay-100">
                        <div className="text-center space-y-2">
                            <div className="inline-block p-1">
                                <span className="text-4xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-blue-400 bg-clip-text text-transparent bg-300% animate-gradient">
                                    Hello, {username}
                                </span>
                            </div>
                            <h3 className="text-2xl font-medium text-gray-400">Where should we start?</h3>
                        </div>

                        {/* Shortcuts Grid */}
                        <div className="flex flex-wrap justify-center gap-3 w-full max-w-2xl px-4">
                            {shortcuts.map((shortcut, idx) => (
                                <button
                                    key={idx}
                                    onClick={shortcut.action}
                                    className="flex items-center gap-2 px-4 py-3 bg-gray-800/50 hover:bg-gray-800 border border-gray-700/50 hover:border-blue-500/30 rounded-full text-left transition-all group shadow-sm hover:shadow-md"
                                >
                                    <span className="text-blue-400 group-hover:text-blue-300 transition-colors">
                                        {shortcut.icon}
                                    </span>
                                    <span className="text-sm font-medium text-gray-300 group-hover:text-white">
                                        {shortcut.text}
                                    </span>
                                </button>
                            ))}
                        </div>

                        {loading && (
                            <div className="flex items-center gap-2 text-blue-400 animate-pulse bg-blue-900/20 px-4 py-2 rounded-full">
                                <Sparkles size={16} />
                                <span className="text-sm font-medium">Processing your video...</span>
                            </div>
                        )}
                    </div>
                ) : (
                    /* Chat History */
                    <div className="w-full max-w-3xl mx-auto space-y-6">
                        {/* If we have a video but no messages yet, show a small "Ready" indicator */}
                        {videoId && messages.length === 0 && (
                            <div className="flex justify-center pb-4">
                                <span className="text-xs font-medium text-gray-500 bg-gray-900/50 px-3 py-1 rounded-full border border-gray-800">
                                    Video Context Loaded
                                </span>
                            </div>
                        )}

                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                                <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center shrink-0
                    ${msg.role === 'user' ? 'bg-blue-600' : 'bg-purple-600'}
                  `}>
                                    {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                                </div>
                                <div className={`
                    max-w-[85%] rounded-2xl px-5 py-3 text-sm leading-relaxed shadow-sm
                    ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-tr-sm'
                                        : 'bg-gray-800 border border-gray-700 text-gray-100 rounded-tl-sm'
                                    }
                  `}>
                                    {msg.content || (isStreaming && idx === messages.length - 1 ? <span className="animate-pulse">Thinking...</span> : '')}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-4 bg-gradient-to-t from-gray-900 via-gray-900 to-transparent">
                <div className="w-full max-w-3xl mx-auto relative group">
                    {/* Action Button (Left) */}
                    <div className="absolute left-2 top-1/2 -translate-y-1/2 z-20">
                        <MenuPopover
                            onUploadVideo={handleUpload}
                            onPlaceholder={(type) => onToast(`${type} upload coming soon!`, 'success')}
                        />
                    </div>

                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                        placeholder={videoId ? "Ask something about the video..." : "Upload a video to start..."}
                        disabled={loading || isStreaming}
                        className="w-full bg-gray-800/80 backdrop-blur-xl text-gray-100 rounded-2xl pl-12 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500/50 border border-gray-700/50 shadow-xl transition-all"
                    />
                    <button
                        onClick={() => handleSend()}
                        disabled={!input.trim() || loading || isStreaming}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-blue-600 rounded-xl text-white hover:bg-blue-500 disabled:opacity-50 disabled:bg-gray-700 transition-all shadow-lg hover:shadow-blue-500/25"
                    >
                        <Send size={18} />
                    </button>
                </div>
                <div className="text-center mt-3 h-4">
                    {isStreaming ? (
                        <span className="text-xs font-mono text-blue-400 animate-pulse">
                            Generating response...
                        </span>
                    ) : (
                        <span className="text-[10px] text-gray-600">
                            Obsidian AI can make mistakes. Verify important info.
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}

function MenuPopover({ onUploadVideo, onPlaceholder }: { onUploadVideo: () => void, onPlaceholder: (t: string) => void }) {
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div className="relative" ref={menuRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`
                    p-2 rounded-full transition-all duration-200
                    ${isOpen ? 'bg-gray-700 text-white rotate-45' : 'text-gray-400 hover:text-white hover:bg-gray-700'}
                `}
                title="Add content"
            >
                <Plus size={20} />
            </button>

            {/* Popover Menu */}
            {isOpen && (
                <div className="absolute bottom-full mb-4 left-0 w-56 bg-gray-800 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in slide-in-from-bottom-2 z-50">
                    <div className="p-1 space-y-1">
                        <button
                            onClick={() => { onUploadVideo(); setIsOpen(false); }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-700/50 rounded-xl text-left transition-colors group"
                        >
                            <span className="p-2 bg-blue-500/10 text-blue-400 rounded-lg group-hover:bg-blue-500/20">
                                <Video size={18} />
                            </span>
                            <span className="text-sm font-medium text-gray-200">Add Video</span>
                        </button>

                        <button
                            onClick={() => { onPlaceholder("Image"); setIsOpen(false); }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-700/50 rounded-xl text-left transition-colors group"
                        >
                            <span className="p-2 bg-purple-500/10 text-purple-400 rounded-lg group-hover:bg-purple-500/20">
                                <ImageIcon size={18} />
                            </span>
                            <span className="text-sm font-medium text-gray-200">Add Image</span>
                        </button>

                        <button
                            onClick={() => { onPlaceholder("Audio"); setIsOpen(false); }}
                            className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-700/50 rounded-xl text-left transition-colors group"
                        >
                            <span className="p-2 bg-green-500/10 text-green-400 rounded-lg group-hover:bg-green-500/20">
                                <AudioLines size={18} />
                            </span>
                            <span className="text-sm font-medium text-gray-200">Add Audio</span>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
