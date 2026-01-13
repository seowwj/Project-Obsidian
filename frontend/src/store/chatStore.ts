/**
 * Zustand store for chat state management
 */

import { create } from "zustand";
import { chatClient, healthClient, sessionClient, historyClient } from "../api/client";
import { ChatRequest } from "../gen/obsidian/v1/obsidian_pb";

export interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: number;
}

export interface Session {
    id: string;
    title: string;
    createdAt: number;
    updatedAt: number;
}

interface ChatStore {
    // Sessions
    sessions: Session[];
    currentSessionId: string | null;

    // Messages
    messages: Message[];
    isStreaming: boolean;

    // Attachment
    pendingAttachment: string | null;

    // Connection
    isConnected: boolean;
    checkConnection: () => Promise<void>;

    // Actions
    fetchSessions: () => Promise<void>;
    createSession: () => Promise<void>;
    selectSession: (id: string) => Promise<void>;
    deleteSession: (id: string) => Promise<void>;
    renameSession: (id: string, title: string) => Promise<void>;
    sendMessage: (text: string) => Promise<void>;
    attachFile: (path: string) => void;
    clearAttachment: () => void;
}

// Generate UUID
const generateId = () => crypto.randomUUID();

export const useChatStore = create<ChatStore>((set, get) => ({
    // Initial state
    sessions: [],
    currentSessionId: null,
    messages: [],
    isStreaming: false,
    pendingAttachment: null,
    isConnected: false,

    // Check connection
    checkConnection: async () => {
        try {
            await healthClient.check({});
            set({ isConnected: true });
        } catch (error) {
            console.error("Health check failed:", error);
            set({ isConnected: false });
        }
    },

    // Fetch sessions
    fetchSessions: async () => {
        try {
            const response = await sessionClient.listSessions({});
            set({
                sessions: response.sessions.map((s: any) => ({
                    id: s.id,
                    title: s.title,
                    createdAt: Number(s.createdAt),
                    updatedAt: Number(s.updatedAt)
                }))
            });
        } catch (error) {
            console.error("Failed to fetch sessions:", error);
        }
    },

    // Create new session
    createSession: async () => {
        try {
            const response = await sessionClient.createSession({ title: "New Chat" });
            if (response.session) {
                const newSession: Session = {
                    id: response.session.id,
                    title: response.session.title,
                    createdAt: Number(response.session.createdAt),
                    updatedAt: Number(response.session.updatedAt),
                };

                set((state) => ({
                    sessions: [newSession, ...state.sessions],
                    currentSessionId: newSession.id,
                    messages: [],
                }));
            }
        } catch (error) {
            console.error("Failed to create session:", error);
            // Fallback for offline mode? Or just error?
            // For now, let's just log.
        }
    },

    // Select session
    selectSession: async (id: string) => {
        set({ currentSessionId: id, messages: [] });

        try {
            const response = await historyClient.getHistory({ sessionId: id });
            const messages: Message[] = response.messages.map((m: any) => ({
                id: m.id,
                role: m.role as "user" | "assistant",
                content: m.content,
                timestamp: Number(m.timestamp)
            }));

            set({ messages });
        } catch (error) {
            console.error("Failed to fetch history:", error);
        }
    },

    // Delete session
    deleteSession: async (id: string) => {
        try {
            await sessionClient.deleteSession({ sessionId: id });
            set((state) => ({
                sessions: state.sessions.filter((s) => s.id !== id),
                currentSessionId: state.currentSessionId === id ? null : state.currentSessionId,
                messages: state.currentSessionId === id ? [] : state.messages,
            }));
        } catch (error) {
            console.error("Failed to delete session:", error);
        }
    },

    // Rename session
    renameSession: async (id: string, title: string) => {
        try {
            await sessionClient.renameSession({ sessionId: id, newTitle: title });
            set((state) => ({
                sessions: state.sessions.map((s) =>
                    s.id === id ? { ...s, title, updatedAt: Date.now() } : s
                ),
            }));
        } catch (error) {
            console.error("Failed to rename session:", error);
        }
    },

    // Send message
    sendMessage: async (text: string) => {
        let { currentSessionId } = get();
        const { pendingAttachment, messages } = get();

        // Create session if none exists
        if (!currentSessionId) {
            await get().createSession();
            currentSessionId = get().currentSessionId;
            if (!currentSessionId) return; // Should not happen unless creation failed
        }

        const sessionId = currentSessionId!;

        // "Inject" file path into user prompt if attached
        let finalMessage = text;
        if (pendingAttachment) {
            finalMessage = `/file:${pendingAttachment} ${text}`;
        }

        // Add user message locally
        const userMessage: Message = {
            id: generateId(),
            role: "user",
            content: finalMessage, // Use formatted message locally
            timestamp: Date.now(),
        };

        set((state) => ({
            messages: [...state.messages, userMessage],
            isStreaming: true,
        }));

        // Create assistant message placeholder
        const assistantMessage: Message = {
            id: generateId(),
            role: "assistant",
            content: "",
            timestamp: Date.now(),
        };

        set((state) => ({
            messages: [...state.messages, assistantMessage],
        }));

        try {
            // Build request with proper protobuf message
            const request = new ChatRequest({
                // Backend expects structured file path for graph routing, AND we send the injected text for history/LLM context
                message: finalMessage,
                sessionId: sessionId,
                filePath: pendingAttachment || undefined,
            });

            // Stream tokens using ConnectRPC
            for await (const response of chatClient.chat(request)) {
                set((state) => ({
                    messages: state.messages.map((m) =>
                        m.id === assistantMessage.id
                            ? { ...m, content: m.content + response.token }
                            : m
                    ),
                    isConnected: true
                }));
            }

            // Auto-generate title from first message if "New Chat"
            const sessions = get().sessions;
            const currentSession = sessions.find((s) => s.id === sessionId);
            // We can rename locally first, then try backend
            if (currentSession?.title === "New Chat" && messages.length === 0) {
                const title = text.slice(0, 30) + (text.length > 30 ? "..." : "");
                get().renameSession(sessionId, title);
            }
        } catch (error) {
            console.error("Chat error:", error);
            set((state) => ({
                messages: state.messages.map((m) =>
                    m.id === assistantMessage.id
                        ? { ...m, content: "Error: Failed to get response. Is the backend running?" }
                        : m
                ),
                isConnected: false
            }));
        } finally {
            set({ isStreaming: false, pendingAttachment: null });
        }
    },

    // Attach file
    attachFile: (path: string) => {
        set({ pendingAttachment: path });
    },

    // Clear attachment
    clearAttachment: () => {
        set({ pendingAttachment: null });
    },
}));
