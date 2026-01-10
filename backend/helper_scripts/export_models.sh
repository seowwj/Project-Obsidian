#!/bin/bash
# Generic Export/Download Script for OpenVINO Models
# Usage: ./export_models.sh "organization/model-name"
# Example 1: ./export_models.sh "OpenVINO/Phi-3-mini-4k-instruct-int4-ov" (Direct Download)
# Example 2: ./export_models.sh "openai/whisper-small" (Export/Convert)

set -e

MODEL_NAME="$1"

if [ -z "$MODEL_NAME" ]; then
    echo "Error: No model name provided."
    echo "Usage: $0 <model-name>"
    exit 1
fi

# 1. Configuration Check
# Default paths
: "${HF_HOME:=$HOME/models/huggingface}"
: "${OBSIDIAN_OV_MODEL_DIR:=$HOME/models/openvino}"

export HF_HOME
export OBSIDIAN_OV_MODEL_DIR

echo "----------------------------------------------------------------"
echo "Config:"
echo "  Model:    $MODEL_NAME"
echo "  HF Cache: $HF_HOME"
echo "  Target:   $OBSIDIAN_OV_MODEL_DIR"
echo "----------------------------------------------------------------"

# Create directories
mkdir -p "$OBSIDIAN_OV_MODEL_DIR"
mkdir -p "$HF_HOME"

# 2. Determine Strategy
SAFE_NAME="${MODEL_NAME//\//_}"
MODEL_PATH="$OBSIDIAN_OV_MODEL_DIR/$SAFE_NAME"

if [ -d "$MODEL_PATH" ] && [ "$(ls -A "$MODEL_PATH")" ]; then
    echo "Target directory already exists and is not empty: $MODEL_PATH"
    echo "Skipping download/export."
    exit 0
fi

# Check for OpenVINO prefix
if [[ "$MODEL_NAME" == OpenVINO/* ]]; then
    echo "Detected Pre-Optimized OpenVINO model."
    echo "Action: Direct Download using huggingface-cli"
    
    if command -v huggingface-cli &> /dev/null; then
        huggingface-cli download "$MODEL_NAME" --local-dir "$MODEL_PATH"
    else
        echo "Error: huggingface-cli not found. Please install huggingface_hub[cli]."
        exit 1
    fi
else
    echo "Detected Standard Model."
    echo "Action: Export/Convert using optimum-cli"
    
    if command -v optimum-cli &> /dev/null; then
         optimum-cli export openvino --trust-remote-code --model "$MODEL_NAME" "$MODEL_PATH"
    else
        echo "Error: optimum-cli not found. Please install optimum-intel[openvino]."
        exit 1
    fi
fi

echo "----------------------------------------------------------------"
echo "Success. Model available at: $MODEL_PATH"
