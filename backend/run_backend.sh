#!/bin/bash
# Bash Startup Script for Obsidian Backend
# Usage: ./run_backend.sh

set -e

# 1. Set Environment Variables
# Using Linux-standard paths relative to HOME as requested
export OBSIDIAN_OV_MODEL_DIR="$HOME/models/openvino"
export HF_HOME="$HOME/models/huggingface"

echo "----------------------------------------------------------------"
echo "Starting Obsidian Backend..."
echo "  OBSIDIAN_OV_MODEL_DIR: $OBSIDIAN_OV_MODEL_DIR"
echo "  HF_HOME:               $HF_HOME"
echo "----------------------------------------------------------------"

# 2. Run Backend as a Package
python -m app.server
