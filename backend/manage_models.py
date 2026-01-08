import os
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target Directories
HF_TARGET_DIR = r"D:\models\HF_download"
OV_TARGET_DIR = r"D:\models\OV_compiled"

# Set HF_HOME before importing transformers/optimum to ensure it takes effect
os.environ["HF_HOME"] = HF_TARGET_DIR
logger.info(f"Set HF_HOME to {HF_TARGET_DIR}")

# Now import the heavy libraries
from app.config import MODEL_IDS
from optimum.intel import OVModelForCausalLM, OVModelForVisualCausalLM, OVModelForSpeechSeq2Seq
from transformers import AutoTokenizer, AutoProcessor

def setup_directories():
    logger.info(f"Creating directories:\n  HF: {HF_TARGET_DIR}\n  OV: {OV_TARGET_DIR}")
    os.makedirs(HF_TARGET_DIR, exist_ok=True)
    os.makedirs(OV_TARGET_DIR, exist_ok=True)

def clear_legacy_cache():
    r"""
    Clears the default HF cache (usually C:\Users\<user>\.cache\huggingface).
    """
    default_cache = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
    if os.path.exists(default_cache):
        logger.info(f"Found legacy cache at {default_cache}. Clearing...")
        try:
            shutil.rmtree(default_cache)
            logger.info("Legacy cache cleared.")
        except Exception as e:
            logger.warning(f"Failed to clear legacy cache: {e}. You may need to delete it manually.")
    else:
        logger.info("No legacy cache found at default location.")

def compile_and_save_models():
    """
    Downloads and compiles models to OpenVINO IR format in OV_TARGET_DIR.
    """
    logger.info("Starting model compilation/download...")
    
    # 1. Generation Model (Phi-3)
    # It is already an OpenVINO model, so we just download (load) and save.
    try:
        gen_id = MODEL_IDS["generation"]
        safe_name = gen_id.replace("/", "_")
        save_path = os.path.join(OV_TARGET_DIR, safe_name)
        
        if not os.path.exists(save_path):
            logger.info(f"Processing Generation Model: {gen_id}")
            model = OVModelForCausalLM.from_pretrained(gen_id, export=False) # It's already OV
            tokenizer = AutoTokenizer.from_pretrained(gen_id)
            
            logger.info(f"Saving to {save_path}...")
            model.save_pretrained(save_path)
            tokenizer.save_pretrained(save_path)
        else:
            logger.info(f"Generation Model already existing at {save_path}")
            
    except Exception as e:
        logger.error(f"Failed to process Generation Model: {e}")

    # 2. Vision Model (SmolVLM2)
    try:
        vis_id = MODEL_IDS["vision"]
        safe_name = vis_id.replace("/", "_")
        save_path = os.path.join(OV_TARGET_DIR, safe_name)
        
        if not os.path.exists(save_path):
            logger.info(f"Processing Vision Model: {vis_id}")
            # export=True forces conversion to OpenVINO IR
            model = OVModelForVisualCausalLM.from_pretrained(vis_id, export=True) 
            processor = AutoProcessor.from_pretrained(vis_id)
            
            logger.info(f"Saving to {save_path}...")
            model.save_pretrained(save_path)
            processor.save_pretrained(save_path)
        else:
             logger.info(f"Vision Model already existing at {save_path}")

    except Exception as e:
        logger.error(f"Failed to process Vision Model: {e}")

    # 3. Audio Model (Whisper)
    try:
        aud_id = MODEL_IDS["audio"]
        safe_name = aud_id.replace("/", "_")
        save_path = os.path.join(OV_TARGET_DIR, safe_name)
        
        if not os.path.exists(save_path):
            logger.info(f"Processing Audio Model: {aud_id}")
            model = OVModelForSpeechSeq2Seq.from_pretrained(aud_id, export=True)
            processor = AutoProcessor.from_pretrained(aud_id)
            
            logger.info(f"Saving to {save_path}...")
            model.save_pretrained(save_path)
            processor.save_pretrained(save_path)
        else:
             logger.info(f"Audio Model already existing at {save_path}")

    except Exception as e:
        logger.error(f"Failed to process Audio Model: {e}")

if __name__ == "__main__":
    print("WARNING: This script will clear your default Hugging Face cache (C: drive) and download models to D: drive.")
    confirm = input("Type 'yes' to proceed: ")
    if confirm.lower() == "yes":
        clear_legacy_cache()
        setup_directories()
        compile_and_save_models()
        print("\nProcess Complete. Models are ready in D:\\models\\OV_compiled")
        print("Set OBSIDIAN_OV_MODEL_DIR environment variable to D:\\models\\OV_compiled to use them.")
    else:
        print("Aborted.")
