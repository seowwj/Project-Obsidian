import logging
from typing import Dict, Any, List, Optional

from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState
from ..vector_store import VectorStore


class ChunkingNode(BaseNode):
    """
    Determines chunking strategy based on audio_usability.
    
    Two modes:
    - Audio-aligned: Merge adjacent Whisper segments (gap ≤ 0.5s, duration ≤ 10s)
    - Vision-driven: Dense temporal chunks (4s with 1s overlap)
    
    Output:
        processing_chunks: List of {start, end, asr_text (optional)}
    """
    # Chunking parameters
    AUDIO_MAX_GAP = 0.5         # Max gap between segments to merge (seconds)
    AUDIO_MAX_DURATION = 10.0   # Max merged chunk duration (seconds)
    VISION_CHUNK_DURATION = 4.0 # Vision chunk duration (seconds)
    VISION_OVERLAP = 1.0        # Overlap between vision chunks (seconds)
    
    def __init__(self, collection_name: str = "asr_segments"):
        super().__init__(model=None, name="chunking_node")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.vector_store = VectorStore(collection_name=collection_name)
        # Also need access to multimodal_chunks for cache checking
        self.multimodal_store = VectorStore(collection_name="multimodal_chunks")
    
    def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        audio_usability = state.get("audio_usability", {})
        media_id = state.get("media_id")
        video_path = state.get("video_path")
        
        if not video_path:
            self.logger.warning("No video_path in state, skipping chunking")
            return {"processing_chunks": []}
        
        # Check if VLM chunks already exist in ChromaDB (cross-session cache)
        if media_id:
            existing_chunks = self.multimodal_store.get_by_metadata({"media_id": media_id})
            if existing_chunks and existing_chunks.get("documents"):
                chunk_count = len(existing_chunks["documents"])
                self.logger.info(f"Found {chunk_count} existing multimodal chunks for media_id: {media_id[:16]}... (using cache)")
                # Return empty chunks to skip VLM processing, but mark as processed
                return {"processing_chunks": [], "vlm_processed": True}
        
        if audio_usability.get("audio_usable"):
            self.logger.info("Audio usable - using audio-aligned chunking")
            chunks = self._create_audio_aligned_chunks(media_id)
        else:
            self.logger.info(f"Audio not usable (classification: {audio_usability.get('classification', 'unknown')}) - using vision-driven chunking")
            chunks = self._create_vision_driven_chunks(video_path)
        
        self.logger.info(f"Created {len(chunks)} chunks for VLM processing")
        return {"processing_chunks": chunks}
    
    def _create_audio_aligned_chunks(self, media_id: str) -> List[Dict[str, Any]]:
        """
        Create chunks aligned with ASR segments.
        
        Merges adjacent segments when:
        - Gap between segments ≤ 0.5s
        - Combined duration ≤ 10s
        
        Returns:
            List of {start, end, asr_text}
        """
        if not media_id:
            self.logger.warning("No media_id provided for audio-aligned chunking")
            return []
        
        # Fetch segments from ChromaDB
        results = self.vector_store.get_by_metadata({"media_id": media_id})
        
        if not results.get("documents"):
            self.logger.warning(f"No segments found in ChromaDB for media_id: {media_id}")
            return []
        
        # Build segment list with metadata
        segments = []
        for doc, meta in zip(results["documents"], results["metadatas"]):
            segments.append({
                "start": meta.get("start", 0),
                "end": meta.get("end", 0),
                "text": doc
            })
        
        # Sort by start time
        segments.sort(key=lambda x: x["start"])
        
        self.logger.debug(f"Merging {len(segments)} ASR segments into chunks...")
        
        # Merge adjacent segments
        merged = []
        current: Optional[Dict] = None
        
        for seg in segments:
            if current is None:
                current = {
                    "start": seg["start"],
                    "end": seg["end"],
                    "asr_text": seg["text"]
                }
            else:
                gap = seg["start"] - current["end"]
                new_duration = seg["end"] - current["start"]
                
                if gap <= self.AUDIO_MAX_GAP and new_duration <= self.AUDIO_MAX_DURATION:
                    # Merge into current chunk
                    current["end"] = seg["end"]
                    current["asr_text"] += " " + seg["text"]
                else:
                    # Finalize current, start new
                    merged.append(current)
                    current = {
                        "start": seg["start"],
                        "end": seg["end"],
                        "asr_text": seg["text"]
                    }
        
        # Don't forget the last chunk
        if current:
            merged.append(current)
        
        self.logger.info(f"Merged {len(segments)} segments into {len(merged)} audio-aligned chunks")
        return merged
    
    def _create_vision_driven_chunks(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Create fixed-interval chunks for videos without usable audio.
        
        Duration: 4 seconds
        Overlap: 1 second
        
        Returns:
            List of {start, end, asr_text: None}
        """
        from ..utils.frame_sampler import get_video_duration
        
        try:
            duration = get_video_duration(video_path)
        except Exception as e:
            self.logger.error(f"Failed to get video duration: {e}")
            return []
        
        step = self.VISION_CHUNK_DURATION - self.VISION_OVERLAP
        
        chunks = []
        start = 0.0
        
        while start < duration:
            end = min(start + self.VISION_CHUNK_DURATION, duration)
            chunks.append({
                "start": start,
                "end": end,
                "asr_text": None  # No ASR context for vision-driven chunks
            })
            start += step
        
        self.logger.info(f"Created {len(chunks)} vision-driven chunks (duration: {duration:.2f}s)")
        return chunks
