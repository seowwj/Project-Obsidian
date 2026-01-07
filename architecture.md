# Project Obsidian Architecture

## 1. Overview
Project Obsidian is a local-first, offline AI desktop application designed to analyze and query short video files. It leverages a multi-agent system powered by local LLMs and self-hosted MCP (Model Context Protocol) servers to perform tasks like transcription, vision analysis, and report generation.

## 2. System Constraints & Requirements
- **Offline Only**: No internet connection required for core functionality.
- **Local Inference**: All models run locally (OpenVINO / Hugging Face).
- **Video Limit**: Optimized for ~1 minute MP4 files.
- **File Limits**: Max 200MB. Supported formats: `.mp4`, `.mkv`, `.mov`, `.avi`.
- **Privacy**: Chat history and data persist locally.
- **Cross-Platform**: Fully supported on Ubuntu (Linux) and Windows.

## 2.1 System Requirements
- **OS**: Linux (Ubuntu 22.04+) or Windows 10/11 (WSL2 recommended).
- **Runtime**: Python 3.10+, Node.js 18+, Rust (latest).
- **System Libraries**:
    - `ffmpeg` (Required for video/audio processing).
      - **Linux**: `sudo apt install ffmpeg`
      - **Windows**: `winget install ffmpeg` (via PowerShell) or download from [ffmpeg.org](https://ffmpeg.org/download.html).
    - `webview2-com-gtk-4.0` (Linux Tauri requirement).

## 3. High-Level Architecture

```mermaid
graph TD
    User[User] -->|Interacts| UI[Frontend (React + Tauri)]
    UI -->|gRPC / IPC| Backend[Python Backend Orchestrator]
    
    subgraph "Python Backend"
        Orchestrator -->|Routes| AgentRouter[Agent Router]
        
        AgentRouter -->|Call| TranscriptionAgent[Transcription Agent]
        AgentRouter -->|Call| VisionAgent[Vision Agent]
        AgentRouter -->|Call| GenerationAgent[Generation Agent]
        
        TranscriptionAgent <-->|MCP| MCP_Audio[MCP Server: Audio]
        VisionAgent <-->|MCP| MCP_Vision[MCP Server: Vision]
        GenerationAgent <-->|MCP| MCP_Doc[MCP Server: Document]
        
        MCP_Audio -->|Inference| Model_Whisper[Whisper (OpenVINO)]
        MCP_Vision -->|Inference| Model_VLM[VLM (OpenVINO/HF)]
        MCP_Doc -->|Gen| Lib_PDF[ReportGen Lib]
    end
    
    Backend -->|Reads/Writes| Storage[(Local DB/FS)]
```

## 4. Components

### 4.1 Frontend (Tauri + React)
- **Framework**: Tauri (Rust-based) for the application shell.
- **UI Library**: React (with a component library like Shadcn/UI or Material UI).
- **Responsibility**: 
  - Render Chat UI.
  - Handle file inputs (Video upload).
  - Display interaction history.
  - Communicate with Python backend (likely via Tauri Sidecar or gRPC over localhost).

### 4.2 Backend (Python Orchestrator)
- **Communication**: gRPC Server.
- **Responsibility**:
  - Accept requests from Frontend.
  - Manage application state.
  - Route user queries to appropriate agents.
  - Manage "Human-in-the-loop" clarifications.
  - **Memory Management**: Dynamically load/unload models to stay within 8GB RAM.

### 4.3 Agentic Layer (MCP)
The system uses the Model Context Protocol (MCP) to standardize tool usage.
- **Key Models (Optimized for Intel iGPU / 8GB RAM)**:
  - **Chat/Reasoning**: `OpenVINO/Phi-3-mini-4k-instruct-int4-ov`. Optimized for Intel iGPU (INT4).
  - **Memory Strategy**: Models are lazy-loaded. Video models (Whisper/Vision) unload immediately after processing. Chat model loads on first use and stays resident for responsiveness.
  - **Vision**: `HuggingFaceM4/SmolVLM-Instruct` (To optimized using `optimum-intel` to OpenVINO INT4). specialized for visual understanding with low vRAM.
  
- **MCP Servers**:
  - **Audio Server**: Exposes `transcribe_video` (Whisper).
  - **Vision Server**: Exposes `analyze_frames` (SmolVLM).
  - **Memory Server (Vector DB)**: Exposes `search_knowledge_context` (ChromaDB).
  - **Document Server**: Exposes `create_pdf`, `create_ppt`.

## 5. Technology Stack & Dependencies

### Frontend
- **Language**: TypeScript
- **Framework**: React + Tauri
- **UI**: Tailwind CSS + Shadcn/UI (user requested "premium" look).
- **Communication**: gRPC-Web / @grpc/grpc-js.

### Backend
- **Language**: Python 3.10+
- **Inference Engine**: `optimum-intel` + `openvino` + `nncf` (Intel iGPU acceleration).
- **Vector Store**: `chromadb` (Lightweight, local, file-based persistence).
- **Dependencies**: `grpcio`, `mcp`, `opencv-python`, `imageio-ffmpeg` (Private binary), `soundfile`, `fpdf`, `python-pptx`, `transformers`, `torch`.


## 6. Data Flow
1. **User Upload**: User selects a video.
2. **Indexing (Background)**:
    - **Aural**: Extract audio -> Whisper (INT8) -> Text -> Chunk -> **Vector DB**.
    - **Visual**: Extract Keyframes (1/sec) -> SmolVLM (INT4) Caption -> Text -> **Vector DB**.
3. **Query**: User asks "What is discussed about X?".
4. **Retrieval**: Orchestrator searches Vector DB for relevant text/captions.
5. **Generation**: 
    - Retrieved context + Query sent to `Phi-3-mini` (INT4).
    - LLM generates response or requests further specific tool usage (e.g., "Create PDF").

## 7. Model Strategy (Memory Constraint: 8GB)
- **Sequential Execution**: Do not load all models at once.
    - *Ingestion Phase*: Load Whisper -> Process -> Unload. Load VLM -> Process -> Unload.
    - *Chat Phase*: Keep Phi-3-mini loaded (~2.5GB). Keep Vector DB connection open (Low RAM).
- **Quantization**: Strict use of INT4/INT8 OpenVINO models to maximize throughput on iGPU and minimize RAM usage.

## 8. Future Roadmap & Improvements
### 8.1 Stats for Nerds (Performance Monitor)
- **Real-time Metrics**: Display CPU, GPU (iGPU), and RAM usage.
- **Inference Speed**: Show tokens/sec for LLM and frames/sec for Vision.
- **Tech**: Use `psutil` (Python) and Tauri system APIs.

### 8.2 Planned Features
- **YouTube Integration**: Direct URL download and processing.
- **Voice Mode**: Real-time STT and TTS for a hands-free experience.
- **Multi-Video RAG**: Query across a library of videos, not just the active one.
- **Timeline Search**: "Find the exact second where X happened" -> Clickable timestamp in chat.
