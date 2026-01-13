/**
 * ConnectRPC client for Obsidian backend
 */

import { createPromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { ChatService, HealthService, SessionService, HistoryService } from "../gen/obsidian/v1/obsidian_connect";
import { ChatRequest, ChatResponse } from "../gen/obsidian/v1/obsidian_pb";

// Create transport to backend
const transport = createConnectTransport({
    baseUrl: "http://localhost:8000",
});

// Create typed clients
export const chatClient = createPromiseClient(ChatService, transport);
export const healthClient = createPromiseClient(HealthService, transport);
export const sessionClient = createPromiseClient(SessionService, transport);
export const historyClient = createPromiseClient(HistoryService, transport);

// Re-export message types
export { ChatRequest, ChatResponse };
