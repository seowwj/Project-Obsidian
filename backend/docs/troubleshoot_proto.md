# Troubleshooting Log - January 2026

## Overview
This document records critical bugs encountered and resolved during the backend/frontend integration phase, specifically related to environment paths, protobuf generation issues, and python package imports.

## 1. Backend Model Paths Reverting to C: Drive

### Symptom
Backend logs showed "Local model not found... Using HF ID", triggering downloads to the default C: drive cache (`C:\Users\seoww\.cache\huggingface`) and causing Out-Of-Memory (OOM) errors or disk space issues.

### Cause
When running the server manually (or via IDE terminal) using `python -m app.server`, the custom environment variables `OBSIDIAN_OV_MODEL_DIR` and `HF_HOME` were not set in the shell session. The `config.py` logic defaults to standard OS paths if these variables are missing.

### Fix
Created startup scripts to strictly enforce environment configuration before launching the python process.

*   **Windows:** `backend/run_backend.ps1`
    ```powershell
    $Env:OBSIDIAN_OV_MODEL_DIR = "D:\models\OV_compiled"
    $Env:HF_HOME = "D:\models\HF_download"
    python -m app.server
    ```
*   **Linux/WSL:** `backend/run_backend.sh`
    ```bash
    export OBSIDIAN_OV_MODEL_DIR="$HOME/models/openvino"
    export HF_HOME="$HOME/models/huggingface"
    python -m app.server
    ```

**Recommendation:** Always use these scripts to start the backend.

---

## 2. Frontend Crash: "Cannot read properties of null (reading 'deserializeBinary')"

### Symptom
The frontend crashed immediately on startup with:
```
Uncaught TypeError: Cannot read properties of null (reading 'deserializeBinary')
    at <stdin> (service_grpc_web_pb.js:262:34)
```
Debugging revealed that `GetStatusResponse` was `null` in the imported `messages` object, even though strictly defined in `service_pb.js`.

### Cause
The generated `service_pb.js` file (Google Protobuf Closure Compiler output) contained a generated line that explicitly nullified the global symbol:
```javascript
goog.exportSymbol('proto.obsidian.GetStatusRequest', null, global);
```
This is likely an artifact of the proto generation tool handling manually patched or "missing" messages, causing the browser to overwrite the valid function definition with `null`.

### Fix
1.  **Removed Null Exports:** Commented out/deleted the `goog.exportSymbol(..., null)` lines in `service_pb.js`.
2.  **Forced Exports:** Added explicit CommonJS exports at the end of `service_pb.js` to bypass `goog.object.extend` ambiguity:
    ```javascript
    // FORCE EXPORT
    exports.GetStatusRequest = proto.obsidian.GetStatusRequest;
    exports.GetStatusResponse = proto.obsidian.GetStatusResponse;
    ```

---

## 3. Backend Import Errors ("ModuleNotFoundError")

### Symptom
Running `python app/server.py` failed with `ImportError: attempted relative import with no known parent package` (specifically when `agents` tried to import `..config`).

### Cause
Running a file directly (`python path/to/file.py`) treats it as a **Script**, setting the `sys.path` root to that file's directory. This breaks relative imports causing them to fail to resolve the parent `app` package.

### Fix
*   **Use Relative Imports:** Updated `server.py` and `orchestrator.py` to use relative imports (e.g., `from . import service_pb2`).
*   **Run as Package:** Changed execution method to `python -m app.server` (running the module `app.server` from the `backend` root). This sets the correct package context.
