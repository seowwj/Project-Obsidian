# Generic Export/Download Script for OpenVINO Models
# Usage: .\export_models.ps1 -ModelName "organization/model-name"
# Example 1: .\export_models.ps1 -ModelName "OpenVINO/Phi-3-mini-4k-instruct-int4-ov" (Direct Download)
# Example 2: .\export_models.ps1 -ModelName "openai/whisper-small" (Export/Convert)

param (
    [Parameter(Mandatory = $true)]
    [string]$ModelName,

    [string]$HfHome = "D:\models\HF_download",
    [string]$OvDir = "D:\models\OV_compiled"
)

$ErrorActionPreference = "Stop"

# 1. Configuration Check
# Allow Environment overrides if parameters not passed explicitly (or default)
if ($Env:HF_HOME) { $HfHome = $Env:HF_HOME }
if ($Env:OBSIDIAN_OV_MODEL_DIR) { $OvDir = $Env:OBSIDIAN_OV_MODEL_DIR }

# Set Env var for this session for tools that use it
$Env:HF_HOME = $HfHome

Write-Host "----------------------------------------------------------------"
Write-Host "Config:"
Write-Host "  Model:   $ModelName"
Write-Host "  HF Cache: $HfHome"
Write-Host "  Target:   $OvDir"
Write-Host "----------------------------------------------------------------"

if (!(Test-Path $OvDir)) {
    Write-Host "Creating target directory..."
    New-Item -ItemType Directory -Force -Path $OvDir | Out-Null
}

if (!(Test-Path $HfHome)) {
    Write-Host "Creating HF cache directory..."
    New-Item -ItemType Directory -Force -Path $HfHome | Out-Null
}

# 2. Determine Strategy
$SafeName = $ModelName -replace "/", "_"
$ModelPath = Join-Path $OvDir $SafeName
$IsPreOptimized = $ModelName.StartsWith("OpenVINO/", [System.StringComparison]::OrdinalIgnoreCase)

if (Test-Path $ModelPath) {
    Write-Host "Target directory already exists: $ModelPath"
    Write-Host "Skipping download/export."
    exit 0
}

# 3. Execution
if ($IsPreOptimized) {
    Write-Host "Detected Pre-Optimized OpenVINO model."
    Write-Host "Action: Direct Download using huggingface-cli"
    
    # Check for CLI tool
    if (Get-Command "hf" -ErrorAction SilentlyContinue) {
        hf download $ModelName --local-dir $ModelPath
    }
    else {
        Write-Error "hf command not found. Please install huggingface_hub[cli]."
    }
}
else {
    Write-Host "Detected Standard Model."
    Write-Host "Action: Export/Convert using optimum-cli"
    
    # Check for CLI tool
    if (Get-Command "optimum-cli" -ErrorAction SilentlyContinue) {
        # Defaults to auto-detecting task. For ambiguous cases, user might need to modify script or we add a -Task param.
        optimum-cli export openvino --trust-remote-code --model $ModelName $ModelPath
    }
    else {
        Write-Error "optimum-cli not found. Please install optimum-intel[openvino]."
    }
}

Write-Host "----------------------------------------------------------------"
Write-Host "Success. Model available at: $ModelPath"
