# Project Obsidian

A fully local AI ecosystem for video summarization and PDF/PPT generation.

## Environment Setup (Development)

### Prerequisites
- Windows OS (Migrated from Ubuntu/WSL)
- Python 3.x (Add to PATH during installation)

### Backend Initialization
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install uv
uv pip install -r requirements.txt
```

## Running the Application

### Start Backend
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.server
```

## Known Limitations
- **iGPU Drivers**: Due to issues with iGPU drivers on older processors within WSL, the development environment has been migrated to pure Windows. This is a known constraint for hardware acceleration support.

## Troubleshooting
### "FFmpeg not found" Error
If you encounter this error during video processing, it typically means `modules` cannot find the system FFmpeg. We have implemented a bypass using a private binary, but if issues persist:
1. Ensure `imageio-ffmpeg` is installed.
2. The `app.server` includes a patch to auto-add the binary to `PATH`. Ensure you run the server via `python -m app.server`.
