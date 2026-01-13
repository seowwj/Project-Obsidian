/**
 * InputBar component for message input and file attachment
 */

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { useChatStore } from "../store/chatStore";
import { open } from "@tauri-apps/plugin-dialog";
import { Plus, X, Send, FileVideo } from "lucide-react";

export function InputBar() {
    const [input, setInput] = useState("");
    const { sendMessage, isStreaming, pendingAttachment, attachFile, clearAttachment } =
        useChatStore();
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = "auto";
            inputRef.current.style.height = `${inputRef.current.scrollHeight + 2}px`;
        }
    }, [input]);

    const handleSend = async () => {
        if (!input.trim() || isStreaming) return;

        const message = input;
        setInput("");
        await sendMessage(message);
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleAttach = async () => {
        try {
            const selected = await open({
                multiple: false,
                filters: [
                    {
                        name: "Media",
                        extensions: ["mp4", "mkv", "mov", "avi", "wav", "mp3", "m4a", "flac"],
                    },
                ],
            });

            if (selected && typeof selected === "string") {
                attachFile(selected);
            }
        } catch (error) {
            console.error("File dialog error:", error);
        }
    };

    // Extract filename from path
    const getFileName = (path: string) => {
        return path.split(/[/\\]/).pop() || path;
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value);
    };

    return (
        <div className="w-full relative">
            {/* Input Capsule */}
            <div className="w-full bg-[var(--bg-secondary)] border border-[var(--border-subtle)] rounded-xl p-3 flex flex-col shadow-md transition-shadow focus-within:shadow-xl focus-within:border-[var(--border-strong)]">

                {/* Attachment Preview (Inside Capsule as Chip) */}
                {pendingAttachment && (
                    <div className="w-full px-2 pt-2 pb-1 animate-in fade-in slide-in-from-bottom-1">
                        <div className="inline-flex items-center gap-3 bg-white/10 border border-[var(--border-subtle)] rounded-lg px-3 py-2 pr-2 max-w-full">
                            <div className="w-8 h-8 rounded-md bg-blue-500/10 text-blue-500 flex items-center justify-center shrink-0">
                                <FileVideo size={16} />
                            </div>
                            <span className="text-sm text-[var(--text-primary)] truncate font-medium max-w-[200px]">
                                {getFileName(pendingAttachment)}
                            </span>
                            <button
                                onClick={clearAttachment}
                                className="p-1 hover:bg-[var(--bg-secondary)] rounded-full text-[var(--text-muted)] hover:text-red-400 transition-colors ml-1"
                            >
                                <X size={14} />
                            </button>
                        </div>
                    </div>
                )}

                {/* Input Row */}
                <div className="w-full flex items-end">
                    {/* Attach Button (+) */}
                    <button
                        onClick={handleAttach}
                        disabled={isStreaming}
                        className="w-10 h-10 mb-4 rounded-lg hover:bg-[var(--bg-tertiary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors flex items-center justify-center shrink-0 disabled:opacity-50"
                        title="Attach file"
                    >
                        <Plus size={22} strokeWidth={2.5} />
                    </button>

                    {/* Text Area */}
                    <div className="flex-1 min-w-0 mt-2">
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={handleInput}
                            onKeyDown={handleKeyDown}
                            placeholder="Send a message"
                            disabled={isStreaming}
                            rows={1}
                            className="w-full bg-transparent text-[var(--text-primary)] placeholder-[var(--text-muted)] resize-none focus:outline-none disabled:opacity-50 text-[16px] max-h-[200px] py-4 px-4 overflow-hidden"
                        />
                    </div>

                    {/* Send Button (Plane) */}
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isStreaming}
                        className={`
                            w-10 h-10 mb-4 rounded-lg flex items-center justify-center transition-all duration-200 shrink-0 ml-1
                            ${!input.trim() || isStreaming
                                ? "bg-[var(--bg-tertiary)] text-[var(--text-muted)] cursor-not-allowed opacity-50"
                                : "bg-[var(--accent-primary)] text-white hover:bg-[var(--accent-hover)] shadow-lg shadow-blue-500/20"
                            }
                        `}
                    >
                        <Send size={20} className={input.trim() && !isStreaming ? "ml-0.5" : ""} fill={input.trim() ? "currentColor" : "none"} />
                    </button>
                </div>
            </div>
        </div>
    );
}
