import os
import logging
import subprocess
import cv2
import torch
import imageio_ffmpeg
import soundfile as sf
from optimum.intel import OVModelForSpeechSeq2Seq
from transformers import AutoProcessor, pipeline

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, model_size="small"):
        """
        Initialize VideoProcessor with OpenVINO (Whisper).
        """
        self.model_size = f"openai/whisper-{model_size}"
        # OpenVINO device: "GPU" for iGPU 
        self.device = "GPU"
        self.pipeline = None

    def load_model(self):
        if self.pipeline is None:
            logger.info(f"Loading Whisper model ({self.model_size}) on {self.device} (OpenVINO)...")
            
            try:
                # Load model with OpenVINO optimization
                model = OVModelForSpeechSeq2Seq.from_pretrained(
                    self.model_size, 
                    export=True, 
                    device=self.device
                )
            except RuntimeError as e:
                logger.warning(f"Failed to load on {self.device}: {e}. Falling back to CPU.")
                self.device = "CPU"
                model = OVModelForSpeechSeq2Seq.from_pretrained(
                    self.model_size, 
                    export=True, 
                    device=self.device
                )
            processor = AutoProcessor.from_pretrained(self.model_size)

            self.pipeline = pipeline(
                "automatic-speech-recognition",
                model=model,
                tokenizer=processor.tokenizer,
                feature_extractor=processor.feature_extractor,
                chunk_length_s=30,
            )
            logger.info("Whisper model loaded on OpenVINO.")

    def unload_model(self):
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Whisper model unloaded.")

    def process_video(self, video_path: str, frame_interval: int = 2):
        """
        Full processing pipeline:
        1. Extract Audio
        2. Transcribe Audio
        3. Extract Frames
        Returns dict with transcription and frame paths.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        logger.info(f"Processing video: {video_path}")
        
        # 1. & 2. Audio Processing
        transcription = self._transcribe(video_path)
        
        # 3. Frame Extraction
        frames = self._extract_frames(video_path, interval=frame_interval)
        
        return {
            "transcription": transcription,
            "frames": frames
        }

    def _transcribe(self, video_path: str):
        """
        Extracts audio and transcribes it using Whisper (OpenVINO).
        """
        if self.pipeline is None:
             self.load_model()

        logger.info("Starting transcription...")
        
        # Extract audio using pure ffmpeg (via imageio-ffmpeg binary)
        audio_path = os.path.splitext(video_path)[0] + ".wav"
        
        if not os.path.exists(audio_path):
             logger.info("Extracting temporary audio file...")
             ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
             
             # Command: ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav
             # We use -y to overwrite, -vn for no video, -ar 16000 for Whisper native rate
             cmd = [
                 ffmpeg_exe,
                 "-y",
                 "-i", video_path,
                 "-vn",
                 "-acodec", "pcm_s16le",
                 "-ar", "16000",
                 "-ac", "1",
                 audio_path
             ]
             
             # Run silently
             subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Bypass ffmpeg_read by loading audio manually into numpy array
        # This prevents transformers from trying to find 'ffmpeg' system binary
        audio_input, sample_rate = sf.read(audio_path)
        
        # Run pipeline with numpy array
        # return_timestamps=True gives us chunks
        result = self.pipeline(audio_input, return_timestamps=True)
        
        mapped_result = {
            "text": result["text"],
            "segments": []
        }
        
        for chunk in result.get("chunks", []):
            start, end = chunk["timestamp"]
            mapped_result["segments"].append({
                "start": start,
                "end": end if end is not None else start + 1.0, 
                "text": chunk["text"]
            })

        logger.info("Transcription complete.")
        return mapped_result

    def _extract_frames(self, video_path: str, interval: int = 1):
        """
        Extracts frames using OpenCV.
        """
        logger.info(f"Extracting frames every {interval}s...")
        
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_dir = os.path.join(os.path.dirname(video_path), "frames", video_name)
        os.makedirs(output_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
             logger.error(f"Failed to open video: {video_path}")
             return []

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 24.0 # Fallback
            
        frame_interval_idx = int(fps * interval)
        frame_paths = []
        
        idx = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if idx % frame_interval_idx == 0:
                # Calculate estimated timestamp
                timestamp = idx / fps
                frame_filename = os.path.join(output_dir, f"frame_{int(timestamp)}.jpg")
                
                # Write frame
                cv2.imwrite(frame_filename, frame)
                frame_paths.append(frame_filename)
                saved_count += 1
            
            idx += 1
            
        cap.release()
        logger.info(f"Extracted {len(frame_paths)} frames using OpenCV.")
        return frame_paths
