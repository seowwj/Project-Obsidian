# Project Obsidian Setup & Configuration Guide

## Installation

### 1. Simple Bundle
Run the provided installer (`.msi` or `.exe`). This will install:
-   The Frontend (UI)
-   The Backend (AI Server, bundled as a sidecar)
-   All necessary dependencies (OpenVINO runtimes, ChromaDB, etc.)

### 2. First Run
When you launch the application for the first time, it will automatically:
-   Create a configuration file at `AppData/Roaming/com.project-obsidian.app/settings.json`.
-   Spawn the backend process in the background.

## Configuration (Model Paths)
By default, the application is configured to look for AI models in `%AppData%/com.project-obsidian.app/ov_models`.

### Setting Up Models
We provide a standalone helper script to download and setup the required AI models for you.
1.  Navigate to the `scripts/` directory.
2.  Run the setup script:
    ```powershell
    .\setup_models.ps1
    ```
    -   This checks for Python installation.
    -   Creates a temporary isolated environment.
    -   Downloads/Exports the models to the default location automatically.

### Manual Configuration (Optional)
If you wish to store models in a custom location (e.g., `E:\AI_Models`):
1.  Run the script with a target: `.\setup_models.ps1 -TargetDir "E:\AI_Models"`
2.  Navigate to `%AppData%\Roaming\com.project-obsidian.app\settings.json`. (If `settings.json` does not exist, please create the file)
3.  Update the paths to point to your new folder:
    ```json
    {
      "OBSIDIAN_OV_MODEL_DIR": "E:\\AI_Models",
      "HF_HOME": "E:\\AI_Models\\hf_cache"
    }
    ```
4.  **Restart the Application** for changes to take effect.
