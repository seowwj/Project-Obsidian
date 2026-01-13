/**
 * ChatArea component displaying messages and input
 */

import { useRef, useEffect } from "react";
import { useChatStore, Message } from "../store/chatStore";
import { InputBar } from "./InputBar";
import { Sparkles, Bot } from "lucide-react";

export function ChatArea() {
    const { messages, isStreaming, currentSessionId } = useChatStore();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);



    return (
        <div className="flex-1 flex flex-col h-full relative z-0 bg-[var(--bg-primary)]">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto w-full scroll-smooth">
                <div className="flex flex-col min-h-full py-6 items-center">
                    {/* Content Container - Responsive Percentage Width */}
                    <div
                        className="w-full max-w-[90%] lg:max-w-[80%] xl:max-w-[70%] flex-1 flex flex-col justify-start px-4"
                        style={{ paddingTop: "80px" }}
                    >
                        {!currentSessionId || (messages.length === 0 && !isStreaming) ? (
                            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center animate-in fade-in duration-500 opacity-60">
                                <div className="w-16 h-16 rounded-2xl bg-[var(--bg-tertiary)] flex items-center justify-center mb-6 border border-[var(--border-subtle)] shadow-sm">
                                    <Sparkles size={32} className="text-[var(--accent-primary)]" />
                                </div>
                                <h2 className="text-2xl font-semibold text-[var(--text-primary)] tracking-tight">
                                    Welcome
                                </h2>
                            </div>
                        ) : (
                            messages.map((message) => (
                                <MessageBubble key={message.id} message={message} />
                            ))
                        )}

                        {/* Show typing indicator only when streaming AND no content has arrived yet */}
                        {isStreaming && (!messages.length || messages[messages.length - 1].role === "user" || !messages[messages.length - 1].content) && (
                            <div
                                className="animate-in fade-in slide-in-from-bottom-2 duration-300 w-full px-1"
                                style={{ marginBottom: "32px" }}
                            >
                                <div className="flex items-center gap-2 mb-2 select-none opacity-90">
                                    <Bot size={16} className="text-[var(--accent-primary)]" />
                                </div>
                                <div
                                    className="w-fit min-w-[60px] bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] rounded-[24px] rounded-tl-sm shadow-sm flex items-center"
                                    style={{ padding: "14px 20px" }}
                                >
                                    <div className="flex items-center gap-1.5 h-6">
                                        <div className="w-2 h-2 rounded-full bg-[var(--text-muted)] animate-bounce [animation-delay:-0.3s]" />
                                        <div className="w-2 h-2 rounded-full bg-[var(--text-muted)] animate-bounce [animation-delay:-0.15s]" />
                                        <div className="w-2 h-2 rounded-full bg-[var(--text-muted)] animate-bounce" />
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} className="h-4" />
                    </div>
                </div>
            </div>

            {/* Input Fixed at Bottom - Matches Messages Structure */}
            <div className="w-full pb-10 pt-6 flex flex-col items-center bg-[var(--bg-primary)]">
                <div className="w-full max-w-[90%] lg:max-w-[80%] xl:max-w-[70%] px-4">
                    <InputBar />
                    <p className="text-center text-[11px] text-[var(--text-muted)] mt-3">
                        Obsidian can make mistakes. Check important info.
                    </p>
                </div>
            </div>
        </div>
    );
}

interface MessageBubbleProps {
    message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
    // Hide empty messages (placeholders)
    if (!message.content) return null;

    const isUser = message.role === "user";

    if (isUser) {
        // Parse for file attachment
        const fileMatch = message.content.match(/^\/file:(.*?) (.*)$/s);
        let filePath: string | null = null;
        let displayText = message.content;

        if (fileMatch) {
            filePath = fileMatch[1];
            displayText = fileMatch[2];
        }

        const getFileName = (path: string) => path.split(/[/\\]/).pop() || path;

        return (
            <div className="flex justify-end w-full group" style={{ marginBottom: "32px" }}>
                <div
                    className="max-w-[80%] rounded-xl rounded-br-sm shadow-sm text-[16px] leading-relaxed whitespace-pre-wrap break-words flex flex-col items-end"
                    style={{ padding: "14px 20px", backgroundColor: "#3A5AF9", color: "white" }}
                >
                    {displayText}

                    {filePath && (
                        <div className="mt-3 flex items-center gap-2 bg-white/10 rounded-lg px-3 py-2 pr-4 max-w-full">
                            <div className="w-8 h-8 rounded-md bg-white/20 flex items-center justify-center shrink-0">
                                {/* Use FileVideo or generic File icon? Importing FileVideo since used in input */}
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /><path d="m10 11 5 3-5 3v-6Z" /></svg>
                            </div>
                            <div className="flex flex-col min-w-0 text-left">
                                <span className="text-sm font-medium truncate max-w-[200px] leading-tight opacity-95">
                                    {getFileName(filePath)}
                                </span>
                                <span className="text-[10px] opacity-70 uppercase tracking-wider font-semibold">
                                    Attached
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // Bot Message (Bubble style restored)
    return (
        <div className="flex flex-col w-full group items-start" style={{ marginBottom: "32px" }}>
            {/* Bot Header (Icon only) */}
            <div className="flex items-center gap-2 mb-2 px-1 select-none opacity-90">
                <Bot size={16} className="text-[var(--accent-primary)]" />
            </div>

            {/* Bot Content Bubble */}
            <div
                className="w-fit max-w-[80%] bg-[var(--bg-tertiary)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-xl rounded-tl-sm shadow-sm text-[16px] leading-relaxed whitespace-pre-wrap break-words"
                style={{ padding: "14px 20px" }}
            >
                {message.content}
            </div>
        </div>
    );
}
