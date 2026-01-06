# Project Obsidian Changelog

## [Unreleased]

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
