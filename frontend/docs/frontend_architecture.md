# Obsidian Frontend Architecture

> **Created**: 2026-01-12  
> **Stack**: Tauri 2.x + Vite + React + TypeScript + Zustand

---

## Table of Contents

1. [Technology Overview](#technology-overview)
2. [Project Setup Steps](#project-setup-steps)
3. [Directory Structure](#directory-structure)
4. [Key Configuration Files](#key-configuration-files)
5. [ConnectRPC Integration](#connectrpc-integration)
6. [State Management](#state-management)
7. [Development Workflow](#development-workflow)

---

## Technology Overview

### Tauri

**What it is**: A framework for building desktop applications using web technologies (HTML, CSS, JavaScript) with a Rust backend.

**Why we use it**:
- **Tiny bundle size**: Uses the system's native webview instead of bundling Chromium (~150MB vs ~5MB)
- **Native performance**: Rust backend for CPU-intensive tasks
- **Cross-platform**: Single codebase for Windows, macOS, Linux
- **Security**: Strict permissions model, no Node.js at runtime

**How it works**:
```
┌─────────────────────────────────────────────┐
│                  Tauri App                  │
├─────────────────┬───────────────────────────┤
│   Rust Backend  │   Webview (Frontend)      │
│   (src-tauri/)  │   (React + Vite)          │
│                 │                           │
│  • File system  │  • UI components          │
│  • Native APIs  │  • State management       │
│  • Plugins      │  • API calls              │
└─────────────────┴───────────────────────────┘
```

### Vite

**What it is**: A next-generation frontend build tool that provides extremely fast development experience.

**Why we use it**:
- **Instant server start**: No bundling during development (uses native ES modules)
- **Lightning fast HMR**: Hot Module Replacement updates in <50ms
- **Optimized builds**: Rollup-based production builds with tree-shaking
- **First-class TypeScript**: Zero-config TypeScript support

**Key concepts**:
```javascript
// vite.config.ts
export default defineConfig({
  plugins: [react(), tailwindcss()],  // Plugin system
  server: { port: 1420 },              // Dev server config
});
```

### Rust (in Tauri)

**What it is**: The compiled language powering Tauri's backend.

**Why it's there**:
- **Tauri plugins**: Dialog, file system, window management written in Rust
- **Security**: Memory-safe by design
- **Performance**: Native speed for heavy computations
- **IPC bridge**: Communicates with frontend via commands

**You don't need to write Rust** for basic apps - Tauri provides plugins. But you can add custom Rust commands if needed:

```rust
// src-tauri/src/lib.rs
#[tauri::command]
fn my_command(input: String) -> String {
    format!("Processed: {}", input)
}
```

### Zustand

**What it is**: A small, fast state management library for React.

**Why we use it** (vs Redux, Context API):
- **Minimal boilerplate**: No reducers, action types, or providers
- **TypeScript-first**: Excellent type inference
- **No React context**: Works outside React components
- **Tiny size**: ~1.5KB gzipped

**How it works**:

```typescript
// Define store
const useStore = create((set, get) => ({
  count: 0,
  increment: () => set(state => ({ count: state.count + 1 })),
}));

// Use in component
function Counter() {
  const count = useStore(state => state.count);
  const increment = useStore(state => state.increment);
  return <button onClick={increment}>{count}</button>;
}
```

---

## Project Setup Steps

### 1. Create Tauri Project

```bash
npm create tauri-app@latest frontend -- --template react-ts --manager npm --yes
cd frontend
npm install
```

This scaffolds:
- React + TypeScript frontend
- Tauri Rust backend (src-tauri/)
- Vite configuration

### 2. Install Dependencies

```bash
# ConnectRPC for type-safe API calls (v1.x for compatibility)
npm install @connectrpc/connect@^1.6.1 @connectrpc/connect-web@^1.6.1 @bufbuild/protobuf@^1.10.0

# State management
npm install zustand

# Styling
npm install -D tailwindcss @tailwindcss/vite

# Tauri plugins
npm install @tauri-apps/plugin-dialog
```

### 3. Configure Tailwind

Add to `vite.config.ts`:
```typescript
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // ...
});
```

Add to `src/index.css`:
```css
@import "tailwindcss";
```

### 4. Generate Proto Stubs

Create `buf.gen.yaml`:
```yaml
version: v2
plugins:
  - remote: buf.build/bufbuild/es:v1.10.0
    out: src/gen
  - remote: buf.build/connectrpc/es:v1.6.1
    out: src/gen
```

Generate:
```bash
buf generate ../proto
```

### 5. Configure Tauri Plugins

Add to `src-tauri/Cargo.toml`:
```toml
[dependencies]
tauri-plugin-dialog = "2"
```

Add to `src-tauri/src/lib.rs`:
```rust
.plugin(tauri_plugin_dialog::init())
```

Add to `src-tauri/capabilities/default.json`:
```json
{
  "permissions": ["dialog:default"]
}
```

---

## Directory Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts          # ConnectRPC client setup
│   ├── components/
│   │   ├── Sidebar.tsx        # Session list
│   │   ├── ChatArea.tsx       # Message display
│   │   └── InputBar.tsx       # Message input
│   ├── gen/                   # Generated proto stubs (gitignore)
│   │   └── obsidian/v1/
│   │       ├── obsidian_pb.js
│   │       └── obsidian_connect.js
│   ├── store/
│   │   └── chatStore.ts       # Zustand state
│   ├── App.tsx                # Main layout
│   ├── index.css              # Tailwind + theme
│   └── main.tsx               # React entry
├── src-tauri/                 # Rust/Tauri backend
│   ├── src/
│   │   ├── lib.rs             # Plugin registration
│   │   └── main.rs            # Entry point
│   ├── capabilities/
│   │   └── default.json       # Permissions
│   ├── Cargo.toml             # Rust dependencies
│   └── tauri.conf.json        # Tauri config
├── buf.gen.yaml               # Proto codegen config
├── vite.config.ts             # Vite configuration
└── package.json
```

---

## Key Configuration Files

### vite.config.ts

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const host = process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [react(), tailwindcss()],
  clearScreen: false,  // Show Rust errors
  server: {
    port: 1420,        // Fixed port for Tauri
    strictPort: true,
    host: host || false,
    watch: {
      ignored: ["**/src-tauri/**"],  // Don't watch Rust files
    },
  },
});
```

### src-tauri/tauri.conf.json

Key settings:
- `identifier`: Unique app ID
- `windows`: Window dimensions, title
- `bundle`: App icons, metadata

### package.json Scripts

```json
{
  "scripts": {
    "dev": "vite",                    // Frontend only
    "build": "vite build",            // Production build
    "tauri": "tauri",                 // Tauri CLI
    "tauri dev": "tauri dev",         // Full app dev mode
    "tauri build": "tauri build"      // Production app
  }
}
```

---

## ConnectRPC Integration

### Client Setup (src/api/client.ts)

```typescript
import { createPromiseClient } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";
import { ChatService } from "../gen/obsidian/v1/obsidian_connect";

const transport = createConnectTransport({
  baseUrl: "http://localhost:8000",
});

export const chatClient = createPromiseClient(ChatService, transport);
```

### Streaming Chat

```typescript
// In Zustand store
for await (const response of chatClient.chat(request)) {
  // Update UI with each streamed token
  set(state => ({
    messages: state.messages.map(m =>
      m.id === messageId
        ? { ...m, content: m.content + response.token }
        : m
    ),
  }));
}
```

---

## State Management

### Store Structure (src/store/chatStore.ts)

```typescript
interface ChatStore {
  // State
  sessions: Session[];
  currentSessionId: string | null;
  messages: Message[];
  isStreaming: boolean;
  pendingAttachment: string | null;

  // Actions
  createSession: () => void;
  selectSession: (id: string) => void;
  sendMessage: (text: string) => Promise<void>;
  attachFile: (path: string) => void;
}
```

### Usage in Components

```tsx
function ChatArea() {
  // Subscribe to specific state slices
  const messages = useChatStore(state => state.messages);
  const isStreaming = useChatStore(state => state.isStreaming);
  
  // Get actions (don't cause re-renders)
  const sendMessage = useChatStore(state => state.sendMessage);
  
  return (/* ... */);
}
```

---

## Development Workflow

### Start Development

```bash
# Terminal 1: Backend
cd backend && .\run_backend.ps1

# Terminal 2: Frontend (Tauri dev mode)
cd frontend && npm run tauri dev
```

### Hot Reload

- **React/CSS changes**: Instant HMR (no refresh needed)
- **Rust changes**: Auto-recompile and restart
- **Proto changes**: Run `buf generate ../proto` then refresh

### Build Production App

```bash
npm run tauri build
```

Output: `src-tauri/target/release/frontend.exe`

---

## Common Issues

### Proto Import Errors

**Symptom**: `No matching export 'proto3'`

**Fix**: Ensure matching package versions:
```bash
npm install @bufbuild/protobuf@^1.10.0 @connectrpc/connect@^1.6.1 @connectrpc/connect-web@^1.6.1
```

### Tauri Dev Doesn't Start

**Fix**: Ensure Rust toolchain is installed:
```bash
rustup update stable
```

### CORS Errors

The backend must allow CORS:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
