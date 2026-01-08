import { Plus, Menu, X, Video, MessageCircle, MoreVertical, Pencil, Trash2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { deleteSession, renameSession } from '../api/client';

interface Session {
    id: string;
    title: string;
    videoId: string | null;
    createdAt: string;
}

interface SidebarProps {
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
    onNewChat: () => void;
    onSelectSession: (id: string) => void;
    onRefreshSessions: () => void;
    sessions: Session[];
    activeSessionId: string | null;
}

export function Sidebar({ isOpen, setIsOpen, onNewChat, onSelectSession, onRefreshSessions, sessions, activeSessionId }: SidebarProps) {
    const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState("");
    const menuRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setMenuOpenId(null);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    useEffect(() => {
        if (editingId && inputRef.current) {
            inputRef.current.focus();
        }
    }, [editingId]);

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to delete this chat session?")) {
            try {
                await deleteSession(id);
                onRefreshSessions();
            } catch (err) {
                console.error("Failed to delete session", err);
            }
        }
        setMenuOpenId(null);
    };

    const startRename = (e: React.MouseEvent, session: Session) => {
        e.stopPropagation();
        setEditingId(session.id);
        setEditTitle(session.title);
        setMenuOpenId(null);
    };

    const handleRenameSubmit = async () => {
        if (!editingId) return;
        try {
            await renameSession(editingId, editTitle);
            setEditingId(null);
            onRefreshSessions();
        } catch (err) {
            console.error("Failed to rename session", err);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleRenameSubmit();
        } else if (e.key === 'Escape') {
            setEditingId(null);
        }
    };

    return (
        <div
            className={`
        ${isOpen ? 'w-64' : 'w-16'} 
        bg-gray-950 border-r border-gray-800 transition-all duration-300 flex flex-col
        shadow-xl z-20
      `}
        >
            {/* Header */}
            <div className="p-4 flex items-center justify-between border-b border-gray-800/50">
                <div className={`font-semibold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent transition-opacity duration-200 ${!isOpen && 'opacity-0 hidden'}`}>
                    Obsidian AI
                </div>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="p-1.5 hover:bg-gray-800 rounded-lg text-gray-400 transition-colors"
                >
                    {isOpen ? <X size={18} /> : <Menu size={18} />}
                </button>
            </div>

            {/* New Chat Button */}
            <div className="p-3">
                <button
                    onClick={onNewChat}
                    className={`
            flex items-center gap-2 w-full p-2.5 
            bg-blue-600 hover:bg-blue-500 active:bg-blue-700
            text-white rounded-xl transition-all shadow-lg hover:shadow-blue-900/20
            ${!isOpen ? 'justify-center' : ''}
          `}
                    title="New Chat"
                >
                    <Plus size={20} />
                    {isOpen && <span className="font-medium text-sm">New Chat</span>}
                </button>
            </div>

            {/* History List */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 space-y-1 scrollbar-thin scrollbar-thumb-gray-800">
                {isOpen && (
                    <div className="px-2 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Recent Chats
                    </div>
                )}

                {sessions.length === 0 && isOpen && (
                    <div className="text-center py-8 text-gray-600 text-sm italic">
                        No recent history
                    </div>
                )}

                {sessions.map((session) => (
                    <div
                        key={session.id}
                        className={`
                            relative group flex items-center rounded-lg transition-colors
                            ${activeSessionId === session.id ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200'}
                        `}
                    >
                        <button
                            onClick={() => onSelectSession(session.id)}
                            className={`
                                flex-1 flex items-center gap-3 p-2.5 text-left w-full
                                ${!isOpen ? 'justify-center' : ''}
                            `}
                            title={!isOpen ? session.title : undefined}
                        >
                            {session.videoId ? <Video size={18} className="shrink-0 text-purple-400" /> : <MessageCircle size={18} className="shrink-0 text-blue-400" />}

                            {isOpen && (
                                <div className="flex flex-col items-start overflow-hidden flex-1 min-w-0">
                                    {editingId === session.id ? (
                                        <input
                                            ref={inputRef}
                                            type="text"
                                            value={editTitle}
                                            onChange={(e) => setEditTitle(e.target.value)}
                                            onBlur={handleRenameSubmit}
                                            onKeyDown={handleKeyDown}
                                            onClick={(e) => e.stopPropagation()}
                                            className="w-full bg-gray-700 text-white text-sm px-1 rounded border border-blue-500 focus:outline-none"
                                        />
                                    ) : (
                                        <>
                                            <span className="truncate text-sm w-full font-medium pr-6">
                                                {session.title}
                                            </span>
                                            <span className="text-[10px] text-gray-600">
                                                {session.createdAt ? new Date(session.createdAt).toLocaleDateString() : ''}
                                            </span>
                                        </>
                                    )}
                                </div>
                            )}
                        </button>

                        {/* Context Menu Trigger */}
                        {isOpen && editingId !== session.id && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setMenuOpenId(menuOpenId === session.id ? null : session.id);
                                }}
                                className={`
                                    absolute right-2 p-1 rounded-md text-gray-500 hover:text-white hover:bg-gray-700
                                    transition-opacity duration-200
                                    ${menuOpenId === session.id ? 'opacity-100 bg-gray-700 text-white' : 'opacity-0 group-hover:opacity-100'}
                                `}
                            >
                                <MoreVertical size={16} />
                            </button>
                        )}

                        {/* Dropdown Menu */}
                        {menuOpenId === session.id && isOpen && (
                            <div
                                ref={menuRef}
                                className="absolute right-0 top-full mt-1 w-32 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 overflow-hidden"
                                style={{ top: '2.5rem', right: '0.5rem' }}
                            >
                                <button
                                    onClick={(e) => startRename(e, session)}
                                    className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white flex items-center gap-2"
                                >
                                    <Pencil size={14} /> Rename
                                </button>
                                <button
                                    onClick={(e) => handleDelete(e, session.id)}
                                    className="w-full text-left px-3 py-2 text-sm text-red-400 hover:bg-gray-700 hover:text-red-300 flex items-center gap-2"
                                >
                                    <Trash2 size={14} /> Delete
                                </button>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
