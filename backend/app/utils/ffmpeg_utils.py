import os
import shutil
import tempfile
import logging

logger = logging.getLogger(__name__)

def ensure_ffmpeg_in_path():
    """
    Ensures that ffmpeg is available in the system PATH.
    If not found, attempts to use imageio_ffmpeg to provide a fallback
    by copying the executable to a temp directory and adding it to PATH.
    """
    # Check if ffmpeg is already in PATH
    if shutil.which("ffmpeg"):
        logger.info("ffmpeg found in system PATH.")
        return

    logger.info("ffmpeg not found in system PATH. Attempting to use imageio_ffmpeg...")
    
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        
        # Create a dedicated temp dir for our ffmpeg alias
        temp_ffmpeg_dir = os.path.join(tempfile.gettempdir(), "obsidian_ffmpeg")
        os.makedirs(temp_ffmpeg_dir, exist_ok=True)
        
        target_ffmpeg = os.path.join(temp_ffmpeg_dir, "ffmpeg.exe")
        
        # Copy if it doesn't exist
        if not os.path.exists(target_ffmpeg):
            logger.info(f"Copying ffmpeg from {ffmpeg_path} to {target_ffmpeg}...")
            shutil.copy(ffmpeg_path, target_ffmpeg)
        
        if temp_ffmpeg_dir not in os.environ["PATH"]:
            logger.info(f"Adding temp ffmpeg dir to PATH: {temp_ffmpeg_dir}")
            os.environ["PATH"] += os.pathsep + temp_ffmpeg_dir
            
    except ImportError:
        logger.warning("imageio_ffmpeg not found. Please install it or ensure ffmpeg is in system PATH.")
    except Exception as e:
        logger.warning(f"Failed to configure ffmpeg from imageio_ffmpeg: {e}")
