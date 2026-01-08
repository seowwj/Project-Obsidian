# Architecture Decision Record: Communication Protocol (gRPC vs. REST/SSE)

## 1. Context
Project Obsidian is a local desktop application using **Tauri (React/TypeScript)** for the frontend and **Python** for the backend.
A critical requirement is **real-time streaming** of text (LLM tokens) to the UI to ensure a "premium" responsive experience.

## 2. Alternatives Analyzed

### Option A: gRPC-Web (via Sonora)
Run the Python gRPC server wrapped in `sonora`, which allows it to handle HTTP/1.1 gRPC-Web requests directly.
*   **Pros**:
    *   Single process (no sidecar proxy needed).
    *   Type-safe contracts (Protobuf) ensuring frontend/backend sync.
*   **Cons**:
    *   `sonora` library is unmaintained.
    *   Requires downgrading `urllib3` to < 2.0, which may conflict with other modern AI libraries.
    *   Browser doesn't support full gRPC (HTTP/2 trailers), hence "gRPC-Web" workarounds.

### Option B: gRPC-Web (via Envoy Proxy)
Run a standard Python gRPC server + a separate Envoy Proxy binary to translate browser traffic.
*   **Pros**:
    *   Industry standard approach.
    *   No Python dependency conflicts.
    *   Highly robust.
*   **Cons**:
    *   Increased complexity: Need to ship and manage an extra binary (Envoy) in the desktop installer.
    *   Overkill for a local-only single-user app.

### Option C: REST + Server-Sent Events (SSE) (via FastAPI)
Use standard HTTP endpoints for actions and SSE for streaming responses.
*   **Pros**:
    *   Native to web browsers (EventSource API).
    *   Native to Python (FastAPI).
    *   Zero extra dependencies or proxies.
    *   Easy to debug (visible in Network tab).
    *   Type safety via Pydantic (similar to Protobuf).
*   **Cons**:
    *   Not as "strict" of a contract as Protobuf (though OpenAPI generation helps).
    *   Slightly more verbose text payload vs binary (negligible for local chat).

## 3. Why gRPC was originally preferred?
gRPC is often favored for "microservices" and "polyglot" environments because:
1.  **Strict Contract**: The `.proto` file is the single source of truth. If the backend changes, the frontend build fails immediately (compile-time safety).
2.  **Performance**: Protocol Buffers (binary) are smaller and faster to parse than JSON.
3.  **Streaming**: gRPC was designed from the ground up for streaming (Server streaming, Client streaming, Bi-directional). REST traditionally struggles with this (requiring WebSockets or SSE).

## 4. How gRPC is used in this Architecture
If selected, the workflow is:
1.  **Define**: We write `service.proto` defining `rpc Chat(Message) returns (stream Chunk)`.
2.  **Generate**:
    *   Run `protoc` to create `server_pb2.py` (for Python).
    *   Run `protoc` to create `client_pb.ts` (for React).
3.  **Implement**:
    *   Backend inherits from the generated class.
    *   Frontend imports the generated client and calls `client.chat(msg)`.
4.  **Runtime**: The browser sends a binary POST request. The server responds with binary chunks. The generated JS client decodes these chunks into objects for the UI.

## 5. Recommendation
While gRPC provides strict contracts, **Option C (FastAPI)** is superior for this specific *local desktop* context because:
1.  It eliminates the "Proxy vs Unmaintained Library" dilemma.
2.  It simplifies the build chain (no `protoc` step for frontend).
3.  It provides the same "Premium" streaming experience via SSE.

**Decision**: Pending User Approval.
