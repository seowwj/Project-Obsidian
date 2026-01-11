"""
Frame Sampler Utility

Extracts frames from video files using ffmpeg (via imageio_ffmpeg fallback).
Uses OpenCV for video metadata (duration, dimensions).
Frames are persisted for debugging and potential re-processing.
"""

import os
import subprocess
import logging
from typing import List, Dict, Any, Optional

from .ffmpeg_utils import ensure_ffmpeg_in_path

logger = logging.getLogger(__name__)

# Lazy import cv2 to avoid startup overhead if not needed
_cv2 = None

def _get_cv2():
    """Lazy load OpenCV (load only when needed)"""
    global _cv2
    if _cv2 is None:
        try:
            import cv2
            _cv2 = cv2
        except ImportError:
            raise ImportError(
                "OpenCV is required for video metadata. "
                "Install with: pip install opencv-python"
            )
    return _cv2


def sample_frames(
    video_path: str,
    start_time: float,
    end_time: float,
    fps: float = 1.0,
    max_frames: int = 12,
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Sample frames from a video within a time window.
    
    Uses ffmpeg (via imageio_ffmpeg fallback) for extraction.
    Frames are persisted in output_dir for debugging/re-processing.
    
    Args:
        video_path: Path to video file
        start_time: Start timestamp in seconds
        end_time: End timestamp in seconds
        fps: Frames per second to extract (default 1.0)
        max_frames: Maximum frames to extract (default 12, SmolVLM2 limit)
        output_dir: Directory to save frames (defaults to sibling 'frames' folder)
    
    Returns:
        List of {timestamp: float, path: str} for each extracted frame
    """
    ensure_ffmpeg_in_path()
    
    # Calculate duration and frame count
    duration = end_time - start_time
    total_frames = min(int(duration * fps) + 1, max_frames)
    
    if total_frames <= 0:
        logger.warning(f"No frames to extract: duration={duration}, fps={fps}")
        return []
    
    # Setup output directory
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(video_path), "frames")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate frame timestamps
    if total_frames == 1:
        timestamps = [start_time]
    else:
        step = duration / (total_frames - 1)
        timestamps = [start_time + i * step for i in range(total_frames)]
    
    frames = []
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    for i, ts in enumerate(timestamps):
        # Output path: {output_dir}/{video_basename}_{start}_{end}_frame{i}.jpg
        frame_path = os.path.join(
            output_dir, 
            f"{video_name}_{start_time:.2f}_{end_time:.2f}_frame{i:03d}.jpg"
        )
        
        # Extract frame using ffmpeg
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(ts),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",  # High quality JPEG
            frame_path
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                check=True,
                timeout=30  # 30 second timeout per frame
            )
            frames.append({"timestamp": ts, "path": frame_path})
            logger.debug(f"Extracted frame at {ts:.2f}s -> {frame_path}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to extract frame at {ts:.2f}s: {e.stderr.decode() if e.stderr else e}")
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout extracting frame at {ts:.2f}s")
    
    logger.info(f"Extracted {len(frames)} frames from {video_path} [{start_time:.2f}-{end_time:.2f}s]")
    return frames


def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds using OpenCV.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Duration in seconds
        
    Raises:
        RuntimeError: If OpenCV fails to get duration
    """
    cv2 = _get_cv2()
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")
        
        # Get frame count and FPS
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        
        cap.release()
        
        if video_fps <= 0:
            raise RuntimeError(f"Invalid FPS ({video_fps}) for video: {video_path}")
        
        duration = frame_count / video_fps
        logger.debug(f"Video duration: {duration:.2f}s (frames={frame_count}, fps={video_fps})")
        return duration
        
    except Exception as e:
        logger.error(f"Failed to get video duration: {e}")
        raise RuntimeError(f"Failed to get video duration: {e}")


def get_media_info(media_path: str) -> Dict[str, Any]:
    """
    Get media file information using OpenCV.
    
    Works for both video and image files.
    
    Args:
        media_path: Path to media file (video or image)
        
    Returns:
        Dict with 'type' ('video' or 'image'), 'duration' (if video), 
        'width', 'height', 'fps' (if video)
    """
    cv2 = _get_cv2()
    
    try:
        # Try opening as video first
        cap = cv2.VideoCapture(media_path)
        
        if cap.isOpened():
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # If it has multiple frames and valid FPS, it's a video
            if frame_count > 1 and video_fps > 0:
                duration = frame_count / video_fps
                return {
                    "type": "video",
                    "duration": duration,
                    "width": width,
                    "height": height,
                    "fps": video_fps,
                    "frame_count": int(frame_count)
                }
        
        # Try opening as image
        img = cv2.imread(media_path)
        if img is not None:
            height, width = img.shape[:2]
            return {
                "type": "image",
                "duration": None,
                "width": width,
                "height": height
            }
        
        raise RuntimeError(f"Could not open media file: {media_path}")
        
    except Exception as e:
        logger.error(f"Failed to get media info: {e}")
        raise RuntimeError(f"Failed to get media info: {e}")

