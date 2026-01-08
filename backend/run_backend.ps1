# PowerShell Startup Script for Obsidian Backend
# Usage: .\run_backend.ps1

$ErrorActionPreference = "Stop"

# 1. Set Environment Variables
# These enforce usage of the D: drive for model storage
$Env:OBSIDIAN_OV_MODEL_DIR = "D:\models\OV_compiled"
$Env:HF_HOME = "D:\models\HF_download"

Write-Host "----------------------------------------------------------------"
Write-Host "Starting Obsidian Backend..."
Write-Host "  OBSIDIAN_OV_MODEL_DIR: $Env:OBSIDIAN_OV_MODEL_DIR"
Write-Host "  HF_HOME:               $Env:HF_HOME"
Write-Host "----------------------------------------------------------------"

# 2. Run Backend as a Package
python -m app.server
