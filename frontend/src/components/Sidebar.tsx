/**
 * Sidebar component with minimalist design
 */

import { useState, useEffect } from "react";
import { useChatStore, Session } from "../store/chatStore";
import {
    Plus,

    Trash2,
    ChevronLeft,
    ChevronRight
} from "lucide-react";

export function Sidebar() {
    const {
        sessions,
        currentSessionId,
        isStreaming,
        createSession,
        selectSession,
        deleteSession,
        isConnected,
        checkConnection,
        fetchSessions
    } = useChatStore();
    const [isCollapsed, setIsCollapsed] = useState(false);

    // Poll for connection status
    useEffect(() => {
        checkConnection(); // Initial check
        fetchSessions();
        const interval = setInterval(checkConnection, 5000); // Check every 5s
        return () => clearInterval(interval);
    }, [checkConnection, fetchSessions]);

    return (
        <aside
            className={`
                h-full bg-[var(--bg-secondary)] border-r border-[var(--border-subtle)] flex flex-col transition-all duration-300 ease-in-out z-20
                ${isCollapsed ? "w-16" : "w-72"}
            `}
        >
            {/* Content Column (The "Green Box") */}
            <div
                className="flex flex-col h-full overflow-hidden"
                style={{ padding: isCollapsed ? "12px 6px" : "16px 32px" }}
            >
                {/* Header & Toggle */}
                <div className={`h-12 flex items-center shrink-0 mb-6 ${isCollapsed ? "justify-center" : "justify-between"}`}>
                    {!isCollapsed && (
                        <h1 className="text-xl font-bold tracking-tight text-[var(--text-primary)]">
                            Obsidian
                        </h1>
                    )}
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className={`
                            p-2 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors
                        `}
                    >
                        {isCollapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
                    </button>
                </div>

                {/* New Chat Button */}
                <button
                    onClick={createSession}
                    className={`
                        flex items-center justify-center gap-2 w-full rounded-xl bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white shadow-lg shadow-blue-500/20 transition-all active:scale-[0.98] shrink-0
                        ${isCollapsed ? "px-0" : ""}
                    `}
                    style={{
                        padding: isCollapsed ? "12px" : "18px 24px",
                        marginBottom: isCollapsed ? "0" : "24px" // Remove margin when collapsed to stack neatly if needed, or keep it. User didn't specify, but often looks better. let's keep consistent spacing logic or adjust.
                        // Actually, user wants to HIDE recent chats.
                    }}
                    title="New Chat"
                >
                    <Plus size={22} strokeWidth={2.5} />
                    {!isCollapsed && <span className="text-base font-semibold">New Chat</span>}
                </button>

                {/* Scrollable List - Hidden when collapsed */}
                {/* Scrollable List - Hidden when collapsed */}
                {isCollapsed ? (
                    <div className="flex-1" />
                ) : (
                    <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0 px-0 mt-6">
                        {sessions.length > 0 && (
                            <div className="px-2 py-2 mb-2">
                                <span className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">
                                    Recent
                                </span>
                            </div>
                        )}

                        <div className="space-y-1 pb-4">
                            {sessions.map((session) => (
                                <SessionItem
                                    key={session.id}
                                    session={session}
                                    isActive={session.id === currentSessionId}
                                    isCollapsed={isCollapsed}
                                    onSelect={() => selectSession(session.id)}
                                    onDelete={() => deleteSession(session.id)}
                                />
                            ))}

                            {sessions.length === 0 && (
                                <div className="flex flex-col items-center justify-center p-8 text-center opacity-60">
                                    <p className="text-sm text-[var(--text-muted)]">No chats history</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Status Footer */}
                <div className={`pt-6 mt-auto border-t border-[var(--border-subtle)] shrink-0 ${isCollapsed ? "flex justify-center border-none pt-4" : ""}`}>
                    <div className={`flex items-center gap-3 ${isCollapsed ? "justify-center" : ""}`}>
                        <div className="relative flex items-center justify-center">
                            <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? (isStreaming ? "bg-[var(--status-warning)]" : "bg-[var(--status-success)]") : "bg-[var(--status-error)]"}`} />
                            {isStreaming && isConnected && (
                                <div className="absolute w-full h-full rounded-full bg-[var(--status-warning)] animate-ping opacity-75" />
                            )}
                        </div>

                        {!isCollapsed && (
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-[var(--text-primary)] leading-tight mb-1">
                                    {isConnected ? (isStreaming ? "Processing..." : "System Online") : "Backend Offline"}
                                </p>
                                <p className="text-xs text-[var(--text-muted)] leading-tight">
                                    {isConnected ? (isStreaming ? "AI is generating" : "Ready to chat") : "Reconnecting..."}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </aside>
    );
}

interface SessionItemProps {
    session: Session;
    isActive: boolean;
    isCollapsed: boolean;
    onSelect: () => void;
    onDelete: () => void;
}

function SessionItem({ session, isActive, isCollapsed, onSelect, onDelete }: SessionItemProps) {
    return (
        <div
            onClick={onSelect}
            className={`
                group flex items-center gap-3 rounded-lg cursor-pointer transition-all duration-200
                ${isActive
                    ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)] font-medium"
                    : "text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)]/50 hover:text-[var(--text-primary)]"
                }
                ${isCollapsed ? "justify-center px-2" : ""}
            `}
            style={{ padding: isCollapsed ? "12px" : "10px 12px" }}
            title={session.title}
        >
            {/* Removed MessageSquare icon as requested */}

            {!isCollapsed && (
                <>
                    <span className="flex-1 truncate text-[15px]">
                        {session.title}
                    </span>

                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete();
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1.5 hover:text-red-400 transition-opacity"
                    >
                        <Trash2 size={16} />
                    </button>
                </>
            )}

            {/* If collapsed, maybe show a dot or something minimal if needed, but user said remove icon.
                We can just show nothing or a small initial if strictly needed, but let's stick to removal for now.
                However, if completely removed, collapsed state is clickable but empty?
                Let's put a small placeholder only when collapsed so it's clickable. */}
            {isCollapsed && (
                <div className={`w-2 h-2 rounded-full ${isActive ? "bg-[var(--accent-primary)]" : "bg-[var(--border-strong)]"}`} />
            )}
        </div>
    );
}
