import logging
import os
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState
from ..vector_store import VectorStore
from ..asr import ASRWrapper
from ..utils.file_utils import compute_sha256

logger = logging.getLogger(__name__)

class ASRNode(BaseNode):
    def __init__(self, model: ASRWrapper, collection_name: str = "asr_segments"):
        super().__init__(model=model, name="asr_node")
        self.logger = logger
        self.model = model # ASRWrapper instance

        # Initialize VectorStore for caching
        self.vector_store = VectorStore(collection_name=collection_name)

    def _analyze_audio_usability(self, text: str, duration: float) -> Dict[str, Any]:
        """
        Analyze heuristics to determine if audio is informational/usable.
        """
        text_clean = text.strip()
        word_count = len(text_clean.split())

        # 1. Silent / Empty
        if not text_clean:
            return {
                "audio_usable": False,
                "classification": "silent",
            }

        # 2. Music / Noise tags (If theres [Music] or other tags)
        if text_clean.startswith("[") and text_clean.endswith("]") and word_count <= 2:
             return {
                "audio_usable": False,
                "classification": "music_or_noise",
            }

        # 3. Density check (Words per second)
        # Informational speech usually has > 0.5 words/sec (very rough heuristic)
        # Exception: "Yes." "No." (Short but usable, but still will have high WPS)
        wps = word_count / duration if duration > 0 else 0

        classification = "informational"
        usable = True

        if wps < 0.2: # Very sparse speech, might be background noise hallucination
             classification = "noise"
             usable = False

        return {
            "audio_usable": usable,
            "classification": classification,
        }

    def _get_cached_segments(self, media_id: str) -> List[Dict]:
        """Retrieve segments from VectorStore if they exist."""
        results = self.vector_store.get_by_metadata(where={"media_id": media_id})

        if not results or not results['ids']:
            return None

        # Reconstruct segments from metadata and documents
        segments = []
        ids = results['ids']
        metadatas = results['metadatas']
        documents = results['documents']

        for i, meta in enumerate(metadatas):
            segments.append({
                "start": meta.get("start"),
                "end": meta.get("end"),
                "text": documents[i],
                # Retrieve optional metadata
                "classification": meta.get("classification"),
                "confidence": meta.get("confidence")
            })

        # Sort by start time
        segments.sort(key=lambda x: x["start"])
        return segments

    def _cache_segments(self, media_id: str, segments: List[Dict], global_metadata: Dict[str, Any]):
        """Save segments to VectorStore"""
        texts = []
        metadatas = []

        for seg in segments:
            text = seg.get("text", "").strip()

            texts.append(text)

            # Combine segment specific metadata with global analysis
            meta = {
                "media_id": media_id,
                "start": seg["start"],
                "end": seg["end"],
                "classification": global_metadata.get("classification", "unknown"),
                "audio_usable": global_metadata.get("audio_usable", False),
            }

            metadatas.append(meta)

        self.vector_store.add_texts(texts=texts, metadatas=metadatas)

    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        self.logger.info(f"--- Node {self.name} processing ---")

        audio_path = state.get("audio_path")
        if not audio_path:
            self.logger.warning("No audio_path found in state. Skipping ASRNode.")
            return {}

        if not os.path.exists(audio_path):
            error_msg = f"Audio file not found at: {audio_path}"
            self.logger.error(error_msg)
            return {"messages": [HumanMessage(content=f"Error: {error_msg}")]}

        # 1. Determine Media ID (Media ID will be provided if origin is from video)
        media_id = state.get("media_id")
        if not media_id:
            self.logger.info("No media_id in state. Computing SHA256...")
            media_id = compute_sha256(audio_path)

        self.logger.info(f"Processing audio: {audio_path} (Media ID: {media_id})")

        # 2. Check Cache
        cached_segments = self._get_cached_segments(media_id)
        transcription_segments = []

        if cached_segments:
            self.logger.info("Found cached transcription segments.")
            transcription_segments = cached_segments
        else:
            self.logger.info("No cache found. Running ASR transcription...")
            # 3. Run ASR Wrapper
            result = self.model.transcribe(audio_path)

            full_text = result.get("full_transcription", "")
            transcription_segments = result.get("chunks", [])

            # 4. Analyze Usability
            # Estimate duration from from last segment of last chunk
            duration = transcription_segments[-1]["end"] if transcription_segments else 0.0
            self.logger.info(f"Duration: {duration}")
            usability = self._analyze_audio_usability(full_text, duration)
            self.logger.info(f"Audio Usability Analysis: {usability}")

            # 5. Save to Cache
            self._cache_segments(media_id, transcription_segments, usability)

        # Construct full text from segments
        full_text = " ".join([seg["text"].strip() for seg in transcription_segments])

        return {
            "media_id": media_id,
            "transcription_segments": transcription_segments,
            "messages": [AIMessage(content=f"I have processed the audio file '{media_id}'.")]
        }
