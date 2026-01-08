import os
import logging

logger = logging.getLogger(__name__)

# Defaults (C:\ based or system default)
# User requested default to be C:\, but overrideable.
# We will use standard HF default if not overridden, which is usually C:\Users\<user>\.cache\huggingface
DEFAULT_HF_HOME = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
DEFAULT_OV_DIR = os.path.join(os.path.expanduser("~"), ".cache", "obsidian", "ov_models")

# Environment Variables Overrides
# The user can set these in their shell or .env to override
HF_HOME = os.getenv("HF_HOME", DEFAULT_HF_HOME)
OV_MODEL_DIR = os.getenv("OBSIDIAN_OV_MODEL_DIR", DEFAULT_OV_DIR)

# Ensure directories exist if using custom paths
if OV_MODEL_DIR:
    try:
        os.makedirs(OV_MODEL_DIR, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create OV_MODEL_DIR at {OV_MODEL_DIR}: {e}")

# Cross-Platform Note:
# To make this fully cross-platform (Linux/Windows), we rely on os.path.join and os.path.expanduser.
# Path separators are handled automatically by Python.
# For specific drive letters (like D:), these are Windows-specific and should be passed via environment variables.

# Model IDs
MODEL_IDS = {
    "generation": "OpenVINO/Phi-3-mini-4k-instruct-int4-ov",
    # "generation": "OpenVINO/Qwen3-0.6B-int4-ov",
    "vision": "HuggingFaceTB/SmolVLM2-500M-Video-Instruct",
    "audio": "openai/whisper-small" 
}

def get_model_path(model_type: str):
    """
    Returns the local path for a compiled OpenVINO model if it exists in OV_MODEL_DIR.
    Otherwise returns the Hugging Face Model ID to allow on-the-fly download/compile.
    """
    model_id = MODEL_IDS.get(model_type)
    if not model_id:
        return None
    
    # Sanitized directory name from model ID
    safe_name = model_id.replace("/", "_")
    local_path = os.path.join(OV_MODEL_DIR, safe_name)
    
    # Check if key files exist (any openvino*.xml)
    # Different models have different names (openvino_model.xml, openvino_language_model.xml, openvino_encoder_model.xml)
    if os.path.exists(local_path):
        for file in os.listdir(local_path):
            if file.startswith("openvino") and file.endswith(".xml"):
                logger.info(f"Using local optimized model at: {local_path}")
                return local_path
    
    logger.info(f"Local model not found at {local_path}. Using HF ID: {model_id}")
    return model_id
