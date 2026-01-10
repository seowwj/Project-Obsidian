import logging
import asyncio
import os
import json
from typing import List, Dict, Any, Union

import librosa
try:
    import openvino_genai
except ImportError:
    openvino_genai = None

from langchain_core.messages import BaseMessage

# App imports
from .base_llm import BaseLLMWrapper
from .config import get_model_path
from .utils.ffmpeg_utils import ensure_ffmpeg_in_path

class ASRWrapper(BaseLLMWrapper):
    """
    Automatic Speech Recognition wrapper using OpenVINO GenAI.
    """
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.model_path = get_model_path("audio")
        self.device = "CPU"
        self.pipeline = None

        if openvino_genai is None:
            raise ImportError("openvino-genai is not installed. Please install it to use ASRWrapper.")

        self.load_model()

    def load_model(self):
        self.logger.info(f"Loading ASR model from {self.model_path} on {self.device} (OpenVINO GenAI)...")

        # Check for ffmpeg
        ensure_ffmpeg_in_path()

        # Validation: Check config.json for "model_type": "whisper"
        config_path = os.path.join(self.model_path, "config.json")
        if not os.path.exists(config_path):
             self.logger.warning(f"No config.json found at {self.model_path}. Skipping model_type validation.")
        else:
             try:
                 with open(config_path, "r", encoding="utf-8") as f:
                     config_data = json.load(f)
                     model_type = config_data.get("model_type", "").lower()
                     if model_type != "whisper":
                         raise ValueError(f"Invalid model_type '{model_type}' in {config_path}. Expected 'whisper'.")
             except Exception as e:
                 self.logger.error(f"Failed to validate config.json: {e}")
                 raise

        # Load Pipeline
        try:
            self.pipeline = openvino_genai.WhisperPipeline(self.model_path, device=self.device)
            self.logger.info(f"ASR model loaded from {self.model_path}.")
        except Exception as e:
            self.logger.error(f"Failed to load OpenVINO GenAI WhisperPipeline: {e}")
            raise

    def unload_model(self):
        self.logger.info("Unloading ASR model")
        self.pipeline = None

    def generate(self, messages: List[BaseMessage]) -> str:
        """
        BaseLLMWrapper requirement. ASR does not generate text from messages.
        """
        raise NotImplementedError("ASRWrapper does not support generate(). Use transcribe() instead.")

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using OpenVINO GenAI.
        Returns dict with "text" and "chunks" and "confidence" if available.
        """
        if self.pipeline is None:
            raise RuntimeError("ASR pipeline not initialized.")

        self.logger.info(f"Transcribing {audio_path}...")

        # Load audio using librosa (OpenVINO GenAI expects raw audio samples)
        try:
            raw_speech, _ = librosa.load(audio_path, sr=16000)
        except Exception as e:
            self.logger.error(f"Failed to load audio file {audio_path}: {e}")
            raise ValueError(f"Failed to load audio file {audio_path}: {e}")

        try:
            result = self.pipeline.generate(
                raw_speech,
                task="transcribe",
                return_timestamps=True,
                logprobs = 1
            )

            formatted_chunks = []
            for chunk in result.chunks:
                c_start = getattr(chunk, "start_ts", 0.0)
                c_end = getattr(chunk, "end_ts", 0.0)
                c_text = getattr(chunk, "text", "")

                formatted_chunks.append({
                    "start": c_start,
                    "end": c_end,
                    "text": c_text
                })

            return {
                "full_transcription": " ".join(result.texts),
                "chunks": formatted_chunks
            }

        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise
