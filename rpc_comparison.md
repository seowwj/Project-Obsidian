# gRPC-Web vs. Connect RPC: A Comparison & Recommendation

Generated with Gemini 3

## Executive Summary
For this project, **Connect RPC is the superior choice**.

The current "gRPC mess" stems from the complexity of the legacy `grpc-web` ecosystem, which requires awkward proxies (or adapters like `sonora`), generates difficult-to-maintain JavaScript/TypeScript code (relying on global namespaces), and forces manual patching to work in modern environments like Vite.

**Connect RPC** was built specifically to solve these issues. It provides a cleaner, type-safe, and browser-native experience while staying 100% compatible with the underlying gRPC logic.

---

## 1. The Current "Mess" (gRPC-Web)

We have encountered significant pain points with the standard gRPC-Web setup:

*   **Complexity**: Requires `sonora` on the backend to translate gRPC-Web to standard gRPC because gRPC cannot run natively in browsers.
*   **Code Generation**: The `protoc-gen-grpc-web` tool generates outdated CommonJS code that struggles with modern bundlers like Vite (hence the "global scope" errors and manual patching we did).
*   **Monkey Patching**: We had to manually edit generated files (`service_pb.js`) to fix missing constructors and type errors. This is fragile and will break if we re-generate the code.
*   **Developer Experience**: The generated client APIs (`client.createSession(...)`) are verbose and don't feel like modern TypeScript.

## 2. The Solution: Connect RPC

[Connect](https://connectrpc.com/) is a family of libraries for building browser and gRPC-compatible APIs. It supports three protocols:
1.  **gRPC**: The standard gRPC protocol.
2.  **gRPC-Web**: The protocol we currently use.
3.  **Connect**: A simple, HTTP-friendly protocol (JSON/Proto over POST) that works everywhere (browsers, cURL, etc.).

### Comparison Table

| Feature | Current Stack (gRPC-Web) | Connect RPC Stack |
| :--- | :--- | :--- |
| **Backend Library** | `grpcio` + `sonora` (Adapter) | `connectrpc` (Python) |
| **Frontend Library** | `grpc-web` + `google-protobuf` | `@connectrpc/connect` + `@connectrpc/connect-web` |
| **Transport** | XHR (XMLHttpRequest) | `fetch` API (Modern Standard) |
| **Code Gen** | CommonJS (Legacy, requires polyfills) | ECMAScript Modules (Modern, Vite-ready) |
| **Type Safety** | Loose/Confusing (requires `.d.ts` hacks) | First-class TypeScript Support |
| **Debugging** | Binary blobs in Network tab | JSON (readable) or Binary |
| **Proxying** | Needs Envoy or `sonora` adapter | None required (works over standard HTTP/1.1 or 2) |

---

## 3. Recommended Migration Path

Migrating to Connect is non-destructive to your business logic (`orchestrator.py`), but completely replaces the "plumbing".

### Backend Changes
Replace `grpcio` and `sonora` with `connectrpc`.

1.  **Install**: `pip install connectrpc`
2.  **Server**: Connect integrates directly with ASGI adapters (like `sonora` did, but natively).
    ```python
    # Simplified Example
    from connectrpc.asgi import ConnectASGIApp
    from app.orchestrator import ObsidianService # Your existing class
    
    app = ConnectASGIApp(services=[ObsidianService()])
    # Run with uvicorn app:app
    ```
3.  **Logic**: Your `ObsidianService` logic remains mostly unchanged, though Connect uses slightly different Request/Response context objects than standard `grpcio`.

### Frontend Changes
This is where the biggest win is. No more `service_pb.js` patching.

1.  **Install**: `npm install @connectrpc/connect @connectrpc/connect-web @bufbuild/protobuf`
2.  **Generate**: Use `buf` (a modern replacement for `protoc`) or standard `protoc` with the `connect-es` plugin.
    *   This generates clean `client.ts` files that export strict types.
3.  **Client Usage**:
    ```typescript
    import { createPromiseClient } from "@connectrpc/connect";
    import { createConnectTransport } from "@connectrpc/connect-web";
    import { ObsidianService } from "./gen/service_connect";
    
    // Create simple transport
    const transport = createConnectTransport({
      baseUrl: "http://localhost:8080",
    });
    
    // Create client
    const client = createPromiseClient(ObsidianService, transport);
    
    // Call API - Standard Promise, no callbacks!
    const response = await client.createSession({ videoId: "..." });
    console.log(response.sessionId);
    ```

## 4. Why We Shouldn't Do It Right Now (But Should Later)

While Connect is superior, migrating right now would require:
1.  **Rewriting `server.py`**: Removing `sonora` and setting up the Connect ASGI app.
2.  **Re-generating Frontend Code**: Deleting all our manual patches and setting up the new generation pipeline.
3.  **Refactoring `client.ts`**: The API signatures will change slightly (though for the better).

**Recommendation**: Finish your current feature set polish using the *now-working* gRPC setup. Once the app features are stable, schedule a "Technical Debt" sprint to migrate to Connect RPC for long-term maintainability.
