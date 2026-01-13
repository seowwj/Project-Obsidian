# Project Obsidian

A fully local AI ecosystem for video summarization and PDF/PPT generation.

## Architecture
See [architecture.md](architecture.md) for a high-level overview of the architecture.

## Installation
1. Set up / install models using `scripts/setup_models.ps1`.
    - To install models to a custom directory, see [setup_guide.md](docs\setup_guide.md)
2. Install using packaged installer exe file. (Get from releases)
    - To use models from a custom dictory, see [setup_guide.md - Manual Configuration section](docs\setup_guide.md#manual-configuration-optional) (need to create `settings.json`)

## Sample Files and Prompts
Sample files are available in [test_media](test_media) directory.

> **Details and screenshots are available at [Report.pdf](Report.pdf)**

1. General chatting (demonstrate general chat function and memory)
    - "My name is <name>"
    - "Do you remember my name?"
2. Video / Audio understanding
    - _Attach mp3 file_ "Summarize the audio"
    - _Attach mp4 file_ "Summarize the video"
    - _Attach mp4 file_ "Is there a graph in the video?"

## Repo Structure
```text
Project-Obsidian/
├── backend/                # Python backend (FastAPI + ConnectRPC)
│   ├── app/
│   │   ├── agents/         # AI agent logic and definitions
│   │   ├── nodes/          # Processing nodes (ASR, VLM, LLM, etc.)
│   │   ├── services/       # Core application services
│   │   ├── tools/          # Tool integrations
│   │   ├── orchestrator.py # Graph orchestration logic
│   │   └── server.py       # Main backend server entry point
│   ├── gen/                # Generated Python protobuf code
│   └── run_backend.ps1     # Startup script
├── frontend/               # Desktop application (Tauri + React + TypeScript)
│   ├── src/
│   │   ├── components/     # React UI components
│   │   ├── gen/            # Generated TypeScript protobuf code
│   │   ├── store/          # State management (Zustand)
│   │   └── App.tsx         # Main application component
│   └── src-tauri/          # Rust backend for Tauri integration
└── proto/                  # Protocol Buffer definitions (.proto shared modules)
```

## Environment Setup (Development)

### Prerequisites
- Windows (in theory should also work with Ubuntu / WSL)
- Python 3.x
- Rust
- Node.js / npm

### Backend Initialization
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install uv
uv pip install -r requirements.txt
```

### Frontend Initialization
```bash
cd frontend
npm install
npm run build
```

## Running the Application (Development)

### Start Backend
```bash
cd backend
.\.venv\Scripts\activate
python -m app.server
```

### Start Frontend
```bash
cd frontend
npm run tauri dev
```

## Known Limitations
- iGPU Drivers: Due to issues with iGPU drivers on older processors within WSL, the development environment has been migrated to pure Windows.

## Troubleshooting
### "FFmpeg not found" Error
If you encounter this error during video processing, it typically means `modules` cannot find the system FFmpeg. We have implemented a bypass using a private binary, but if issues persist:
1. Ensure `imageio-ffmpeg` is installed.
2. The `app.server` includes a patch to auto-add the binary to `PATH`. Ensure you run the server via `python -m app.server`.
