# Project Obsidian Changelog

## [Unreleased]

### Fixed
- **Video Deduplication**: Implemented SHA-256 hashing for uploads. Existing videos (by content) are detected, and their ID is returned immediately, preventing re-processing and DB duplication. Added `video_hash` column to `videos` table.
- **Scoped Retrieval**: Updated vector search to strictly filter by `video_id`, determining the context window solely by the active video.
- **Chat-First UI Overhaul**:
    - Replaced blocking "Upload" screen with an always-available Chat Interface.
    - Implemented a collapsible Sidebar and Main Layout.
    - Added "Gemini-style" empty state with shortcut chips (e.g., "Analyze a video") and a personalized "Hello, [Name]" greeting.
    - Integrated `whoami` crate in Tauri backend to fetch the system's Real Name for the greeting.
    - Added a `(+)` menu for media actions (Video, Image, Audio) directly in the input bar.
- **Code Cleanup**: Removed legacy `VideoUpload.tsx` component as upload logic is now integrated into `ChatArea.tsx`.

### Added
- **Session Management**:
    - **Backend**: Implemented `RenameSession` RPC and updated database to support session renaming.
    - **Frontend API**: Updated `client.ts` to support `createSession`, `listSessions`, `deleteSession`, and `renameSession`.
    - **Sidebar**: Added context menu (3 dots) to session items for **Rename** and **Delete** actions.
- **Protobuf Patching**: Manually patched `service_pb.js` and `service_grpc_web_pb.js` to support new RPCs without full regeneration, fixing type errors and constructor issues.

### Fixed
- **Environment**: Added `tauri` script to `package.json` to fix `npm run tauri dev` error.
- **Backend Server**: Refactored `server.py` to use `sonora.asgi` and `uvicorn`, resolving `ImportError: cannot import name 'SonoraWeb'`.
- **System Dependencies**: Installed missing Rust toolchain and Linux system libraries (`libwebkit2gtk-4.1-dev`, etc.) to fix Tauri build linker errors.
- **Tailwind CSS**: Updated `postcss.config.js` to use `@tailwindcss/postcss` for compatibility with Vite.
- **Runtime**: Added `window.global`, `window.exports`, and `window.module` polyfills in `index.html` to support legacy `google-protobuf` generated code in the browser. Also installed `@originjs/vite-plugin-commonjs`.
- **imports**: Refactored `client.ts` to access `ObsidianServiceClient` and messages via `(window as any).proto.obsidian` to completely bypass Vite/CommonJS module interop issues with the generated code.
- **Protobuf Stub**: Patched `service_grpc_web_pb.js` to clone immutable exports (`Object.assign`) and fallback to global namespace access, resolving `TypeError: Attempted to assign to readonly property` and `TypeError: undefined is not an object`.
- **Styling**: Updated `index.css` to use Tailwind v4 syntax (`@import "tailwindcss";`) replacing the broken v3 directives.
- **Backend CORS**: Disabled `sonora`'s internal CORS handling (which caused `TypeError` with `uvicorn`) and replaced it with `starlette.middleware.cors.CORSMiddleware`.
- **Chat Duplication**: Fixed React state mutation bug in `App.tsx` that caused duplicated text when streaming responses (especially in Strict Mode).
- **UI Feedback**: Added a Toast notification system to provide clear feedback on actions like "Video uploaded successfully".

### Added
- **Documentation**: Created `CHANGELOG.md` to track changes and rationale.
- **Security**: Added `SECURITY.md` to document low-risk build-time npm vulnerabilities.

### Known Issues
- None at the moment.
