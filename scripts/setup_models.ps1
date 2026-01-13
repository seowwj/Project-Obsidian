<#
.SYNOPSIS
    Standalone setup script for Project Obsidian Models.
    Creates a dedicated virtual environment and uses CLI tools to download/export models.

.DESCRIPTION
    1. Checks for Python.
    2. Creates a local virtual environment (.model_setup_venv).
    3. Installs 'uv' and required ML libraries (optimum-intel, openvino, etc.).
    4. Downloads pre-compiled models via huggingface-cli.
    5. Exports PyTorch models to OpenVINO via optimum-cli.

.PARAMETER TargetDir
    The directory where models should be stored. Defaults to 'D:\models\OV_compiled'.
#>

param (
    [string]$TargetDir
)

# Default to AppData path for Project Obsidian
$DefaultPath = "$env:APPDATA\com.project-obsidian.app\ov_models"

if ([string]::IsNullOrWhiteSpace($TargetDir)) {
    Write-Host "Default path: $DefaultPath" -ForegroundColor Gray
    $InputPath = Read-Host "Enter target directory (Press Enter to use default)"
    
    if ([string]::IsNullOrWhiteSpace($InputPath)) {
        $TargetDir = $DefaultPath
    }
    else {
        $TargetDir = $InputPath
    }
}

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$RootDir = "$ScriptDir\.."
$VenvName = ".model_setup_venv"
$VenvDir = "$ScriptDir\$VenvName"

# --- Configuration ---
$Models = @{
    "chat"   = @{ "id" = "OpenVINO/Phi-3-mini-4k-instruct-int4-ov"; "type" = "download" }
    "vision" = @{ "id" = "HuggingFaceTB/SmolVLM2-500M-Video-Instruct"; "type" = "export"; "task" = "image-text-to-text" }
    "audio"  = @{ "id" = "openai/whisper-small"; "type" = "export"; "task" = "automatic-speech-recognition" }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Project Obsidian - Model Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Target Directory: $TargetDir"

# Setup Virtual Environment (or use existing one)
$VenvPython = "$VenvDir\Scripts\python.exe"
$VenvPip = "$VenvDir\Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    $PythonExe = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $PythonExe) {
        Write-Error "Python not found! Please install Python 3.10+."
        exit 1
    }
    Write-Host "Creating virtual environment ($VenvName) using $PythonExe..." -ForegroundColor Yellow
    & $PythonExe -m venv $VenvDir
}
else {
    Write-Host "Using existing virtual environment: $VenvDir" -ForegroundColor Gray
}

# Source virtual environment
. "$VenvDir\Scripts\Activate.ps1"

# Install Dependencies with uv
Write-Host "Installing dependencies..." -ForegroundColor Yellow
# Ensure pip is up to date first
& $VenvPython -m pip install --upgrade pip

# Install uv inside the venv
& $VenvPip install uv

# Use uv to install heavy ML libs
$UvExe = "$VenvDir\Scripts\uv.exe"
& $UvExe pip install huggingface_hub[cli] "optimum-intel[openvino,nncf]" torch transformers --upgrade

# Process Models
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

foreach ($key in $Models.Keys) {
    $info = $Models[$key]
    $modelId = $info["id"]
    $safeName = $modelId -replace "/", "_"
    $modelDir = Join-Path $TargetDir $safeName

    Write-Host "`n[Processing $key model] $modelId" -ForegroundColor Magenta
    
    if ((Test-Path $modelDir) -and (Get-ChildItem $modelDir).Count -gt 0) {
        Write-Host "  -> Directory exists and is not empty. Skipping." -ForegroundColor Gray
        continue
    }

    if ($info["type"] -eq "download") {
        Write-Host "  -> Downloading pre-compiled model..."
        & hf download $modelId --local-dir $modelDir
    }
    elseif ($info["type"] -eq "export") {
        Write-Host "  -> Exporting to OpenVINO (this will take time)..."
        $task = $info["task"]
        & optimum-cli export openvino --model $modelId --task $task $modelDir --trust-remote-code
    }
}

Write-Host "`nSUCCESS: Model setup complete!" -ForegroundColor Green
Write-Host "Models are located in: $TargetDir" -ForegroundColor Green
