import logging
import os
import re
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage
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
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = model

        # Initialize VectorStore for caching
        self.vector_store = VectorStore(collection_name=collection_name)

    def _analyze_audio_usability(self, text: str, segments: list, duration: float) -> Dict[str, Any]:
        """
        Analyze heuristics to determine if audio is informational/usable.

        Heuristics applied (in order):
        1. Empty/Silent detection
        2. Non-speech tag detection ([Music], [Applause], etc.)
        3. Word density (words per second)
        4. Vocabulary diversity (unique words / total words)
        5. Repeated phrase detection (hallucination indicator)

        Returns:
            dict with audio_usable (bool), classification (str), and diagnostics (dict)
        """
        text_clean = text.strip()
        words = text_clean.lower().split()
        word_count = len(words)

        diagnostics = {}

        # 1. Silent / Empty
        if not text_clean:
            return {
                "audio_usable": False,
                "classification": "silent",
                "diagnostics": {"reason": "empty_transcription"}
            }

        # 2. Non-speech tag detection ([Music], [Applause], etc.)
        # Whisper outputs these for non-speech audio
        tag_pattern = r'^\[.*\]$'
        if re.match(tag_pattern, text_clean) and word_count <= 2:
            return {
                "audio_usable": False,
                "classification": "music_or_noise",
                "diagnostics": {"reason": "non_speech_tag", "tag": text_clean}
            }

        # 3. Word density (words per second)
        wps = word_count / duration if duration > 0 else 0
        diagnostics["words_per_second"] = round(wps, 2)

        if wps < 0.2:  # Very sparse speech
            return {
                "audio_usable": False,
                "classification": "noise",
                "diagnostics": {**diagnostics, "reason": "low_word_density"}
            }

        # 4. Vocabulary diversity (unique words / total words)
        unique_words = set(words)
        vocab_diversity = len(unique_words) / word_count if word_count > 0 else 0
        diagnostics["vocabulary_diversity"] = round(vocab_diversity, 2)

        # Very low diversity with many words suggests repetitive hallucination
        if vocab_diversity < 0.3 and word_count > 20:
            return {
                "audio_usable": False,
                "classification": "noise",
                "diagnostics": {**diagnostics, "reason": "low_vocabulary_diversity"}
            }

        # 5. Repeated phrase detection (hallucination indicator)
        # Whisper hallucinations often loop the same phrase
        repeated_phrases = self._detect_repeated_phrases(text_clean)
        diagnostics["repeated_phrases"] = repeated_phrases

        if repeated_phrases:
            # If more than 30% of content is repeated phrases, flag as suspicious
            repeated_word_count = sum(len(phrase.split()) * count for phrase, count in repeated_phrases.items())
            repetition_ratio = repeated_word_count / word_count if word_count > 0 else 0
            diagnostics["repetition_ratio"] = round(repetition_ratio, 2)

            if repetition_ratio > 0.3:
                return {
                    "audio_usable": False,
                    "classification": "noise",
                    "diagnostics": {**diagnostics, "reason": "excessive_repetition"}
                }

        # 6. Per-segment quality check
        flagged_segments = self._analyze_segments_quality(segments)
        diagnostics["flagged_segments"] = len(flagged_segments)

        # If more than 50% of segments are flagged, consider audio unreliable
        if segments and len(flagged_segments) > len(segments) * 0.5:
            return {
                "audio_usable": False,
                "classification": "noise",
                "diagnostics": {**diagnostics, "reason": "many_flagged_segments"}
            }

        return {
            "audio_usable": True,
            "classification": "informational",
            "diagnostics": diagnostics
        }

    def _detect_repeated_phrases(self, text: str, min_phrase_words: int = 3, min_repeats: int = 3) -> Dict[str, int]:
        """
        Detect repeated phrases that may indicate Whisper hallucination.
        Example:
        - Partial sentence loops

        Returns:
            dict mapping repeated phrases to their occurrence count
        """
        words = text.lower().split()
        phrase_counts = {}

        # Check phrases of various lengths (3-6 words)
        for phrase_len in range(min_phrase_words, min(7, len(words) + 1)):
            for i in range(len(words) - phrase_len + 1):
                phrase = " ".join(words[i:i + phrase_len])
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

        # Filter to only phrases that repeat min_repeats times
        repeated = {phrase: count for phrase, count in phrase_counts.items() if count >= min_repeats}

        # Remove subphrases if a longer phrase contains them with same count
        filtered = {}
        for phrase, count in sorted(repeated.items(), key=lambda x: -len(x[0])):
            is_subphrase = False
            for longer_phrase in filtered:
                if phrase in longer_phrase and filtered[longer_phrase] >= count:
                    is_subphrase = True
                    break
            if not is_subphrase:
                filtered[phrase] = count

        return filtered

    def _analyze_segments_quality(self, segments: List[Dict]) -> List[Dict]:
        """
        Analyze individual segments for quality issues.

        Flags segments with:
        - Duration anomalies (very long duration with little text)
        - Very sparse segments (few words spoken / second (currently set at 0.1))

        Returns:
            list of flagged segments with reasons
        """
        flagged = []

        for seg in segments:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "").strip()

            duration = end - start
            word_count = len(text.split())

            issues = []

            # Duration anomaly: long segment with few words
            if duration > 10 and word_count < 3:
                issues.append("duration_anomaly")

            # Very sparse: less than 0.1 words per second
            if duration > 0 and word_count / duration < 0.1:
                issues.append("very_sparse")

            if issues:
                flagged.append({
                    "start": start,
                    "end": end,
                    "text": text,
                    "issues": issues
                })

        return flagged

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
                "classification": meta.get("classification"),
                "audio_usable": meta.get("audio_usable", False),  # Include for cache reconstruction
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

    def _extract_audio_from_video(self, video_path: str) -> str:
        """
        Extract audio from video file using ffmpeg.

        Args:
            video_path: Path to video file

        Returns:
            Path to extracted audio file, or None if extraction fails
        """
        import subprocess
        import tempfile
        from ..utils.ffmpeg_utils import ensure_ffmpeg_in_path

        ensure_ffmpeg_in_path()

        # Create output path in temp directory
        video_basename = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(tempfile.gettempdir(), f"{video_basename}_audio.wav")

        # Skip if already extracted
        if os.path.exists(audio_path):
            self.logger.info(f"Using cached extracted audio: {audio_path}")
            return audio_path

        self.logger.info(f"Extracting audio from video: {video_path} -> {audio_path}")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,        # Input video file
            "-vn",                   # No video
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", "16000",          # 16kHz for Whisper
            "-ac", "1",              # Mono audio (for Whisper)
            audio_path               # Output audio file
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                timeout=300  # 5 minute timeout
            )
            self.logger.info(f"Audio extraction complete: {audio_path}")
            return audio_path
        except subprocess.CalledProcessError as e:
            self.logger.error(f"ffmpeg audio extraction failed: {e.stderr.decode() if e.stderr else e}")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error("ffmpeg audio extraction timed out")
            return None
        except Exception as e:
            self.logger.error(f"Audio extraction failed: {e}")
            return None

    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        self.logger.info(f"--- Node {self.name} processing ---")

        audio_path = state.get("audio_path")
        video_path = state.get("video_path")

        # If no audio_path but video_path exists, extract audio from video
        if not audio_path and video_path:
            self.logger.info(f"No audio_path, extracting audio from video: {video_path}")
            audio_path = self._extract_audio_from_video(video_path)
            if not audio_path:
                self.logger.warning("Failed to extract audio from video. Skipping ASRNode.")
                return {"audio_usability": {"audio_usable": False, "classification": "extraction_failed"}}

        if not audio_path:
            self.logger.warning("No audio_path found in state. Skipping ASRNode.")
            return {}

        if not os.path.exists(audio_path):
            error_msg = f"Audio file not found at: {audio_path}"
            self.logger.error(error_msg)
            return {"messages": [HumanMessage(content=f"Error: {error_msg}")]}

        # 1. Determine Media ID
        # Priority: existing state > video_path > audio_path
        # Use video hash when available so audio and video share the same ID
        media_id = state.get("media_id")
        if not media_id:
            if video_path and os.path.exists(video_path):
                self.logger.info("Computing media_id from video_path...")
                media_id = compute_sha256(video_path)
            else:
                self.logger.info("Computing media_id from audio_path...")
                media_id = compute_sha256(audio_path)

        self.logger.info(f"Processing audio: {audio_path} (Media ID: {media_id})")

        # 2. Check Cache
        cached_segments = self._get_cached_segments(media_id)

        if cached_segments:
            self.logger.info(f"Found {len(cached_segments)} cached transcription segments.")
            # Reconstruct usability metadata from cache
            # Read actual values from cached metadata - do NOT assume usable
            first_segment = cached_segments[0] if cached_segments else {}
            duration = cached_segments[-1].get("end", 0.0) if cached_segments else 0.0
            usability = {
                "audio_usable": first_segment.get("audio_usable", False),  # Read from cache
                "classification": first_segment.get("classification", "unknown"),
                "segment_count": len(cached_segments),
                "duration": duration,
                "diagnostics": {"source": "cache"}
            }
        else:
            self.logger.info("No cache found. Running ASR transcription...")
            # 3. Run ASR Wrapper
            result = self.model.transcribe(audio_path)

            full_text = result.get("full_transcription", "")
            transcription_segments = result.get("chunks", [])

            # 4. Analyze Usability
            # Estimate duration from last segment
            duration = transcription_segments[-1]["end"] if transcription_segments else 0.0
            self.logger.info(f"Duration: {duration}")
            usability = self._analyze_audio_usability(full_text, transcription_segments, duration)

            # Add segment_count and duration to usability for state metadata
            usability["segment_count"] = len(transcription_segments)
            usability["duration"] = duration

            self.logger.info(f"Audio Usability Analysis: {usability}")

            # 5. Save to Cache (ChromaDB)
            self._cache_segments(media_id, transcription_segments, usability)

        # Return lightweight state updates only
        # Segments are stored in ChromaDB, accessed via media_id
        return {
            "media_id": media_id,
            "audio_usability": usability,
        }
