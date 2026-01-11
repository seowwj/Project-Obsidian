import os
import shutil
import tempfile
import logging

logger = logging.getLogger(__name__)

# Shared temp directory for ffmpeg binaries
_TEMP_FFMPEG_DIR = os.path.join(tempfile.gettempdir(), "obsidian_ffmpeg")


def ensure_ffmpeg_in_path():
    """
    Ensures that ffmpeg is available in the system PATH.

    If not found, attempts to use imageio_ffmpeg to provide a fallback
    by copying the executable to a temp directory (as ffmpeg.exe) and
    adding it to PATH.

    Note: imageio_ffmpeg bundles ffmpeg with a versioned name like
    'ffmpeg_v7_1.exe', so we copy and rename it to 'ffmpeg.exe'.
    """
    # Check if already in PATH
    if shutil.which("ffmpeg"):
        logger.debug("ffmpeg found in system PATH.")
        return

    logger.info("ffmpeg not found in system PATH. Attempting to use imageio_ffmpeg...")

    try:
        import imageio_ffmpeg

        # Get the actual ffmpeg path (versioned name like ffmpeg_v7_1.exe)
        source_path = imageio_ffmpeg.get_ffmpeg_exe()

        if not os.path.exists(source_path):
            logger.warning(f"imageio_ffmpeg binary not found at: {source_path}")
            return

        # Create temp directory
        os.makedirs(_TEMP_FFMPEG_DIR, exist_ok=True)

        # Target path: rename to ffmpeg.exe (or ffmpeg on Linux)
        target_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        target_path = os.path.join(_TEMP_FFMPEG_DIR, target_name)

        # Copy if it doesn't exist
        if not os.path.exists(target_path):
            logger.info(f"Copying ffmpeg from {source_path} to {target_path}...")
            shutil.copy(source_path, target_path)

        # Add to PATH if not already there
        if _TEMP_FFMPEG_DIR not in os.environ["PATH"]:
            logger.info(f"Adding temp ffmpeg dir to PATH: {_TEMP_FFMPEG_DIR}")
            os.environ["PATH"] = _TEMP_FFMPEG_DIR + os.pathsep + os.environ["PATH"]

    except ImportError:
        logger.warning("imageio_ffmpeg not found. Please install it or ensure ffmpeg is in system PATH.")
    except Exception as e:
        logger.warning(f"Failed to configure ffmpeg from imageio_ffmpeg: {e}")
