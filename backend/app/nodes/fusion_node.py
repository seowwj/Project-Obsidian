import logging
from typing import Dict, Any

from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState
from ..vector_store import VectorStore


class FusionNode(BaseNode):
    """
    Combine ASR + VLM into unified text chunks and store in ChromaDB.

    Output format (audio+visual):
        [00:12-00:18]
        Instruction: Press and hold the power button.
        Visual: The presenter presses the laptop power button.

    Output format (visual-only):
        [00:22-00:29]
        The user presses and holds the reset button.

    Input state:
        vlm_results: List[{start, end, visual_description, asr_text, frame_count}]
        media_id: str
        audio_usability: Dict

    Output state:
        vlm_processed: bool
    """

    def __init__(self, collection_name: str = "multimodal_chunks"):
        """
        Initialize Fusion Node.

        Args:
            collection_name: ChromaDB collection to store fused chunks
        """
        super().__init__(model=None, name="fusion_node")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.vector_store = VectorStore(collection_name=collection_name)

    def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        vlm_results = state.get("vlm_results", [])
        media_id = state.get("media_id")
        audio_usability = state.get("audio_usability", {})

        if not vlm_results:
            self.logger.warning("No VLM results to fuse")
            return {"vlm_processed": False}

        if not media_id:
            self.logger.warning("No media_id in state, cannot store fused chunks")
            return {"vlm_processed": False}

        fused_texts = []
        fused_metadatas = []

        for result in vlm_results:
            fused_text = self._format_fused_chunk(result)
            metadata = self._build_metadata(result, media_id, audio_usability)

            fused_texts.append(fused_text)
            fused_metadatas.append(metadata)

        # Store in ChromaDB
        try:
            self.vector_store.add_texts(texts=fused_texts, metadatas=fused_metadatas)
            self.logger.info(f"Stored {len(fused_texts)} fused multimodal chunks in ChromaDB")
            return {"vlm_processed": True}
        except Exception as e:
            self.logger.error(f"Failed to store fused chunks: {e}")
            return {"vlm_processed": False}

    def _format_fused_chunk(self, result: Dict[str, Any]) -> str:
        """
        Format chunk into unified text representation.

        Args:
            result: VLM result dict with start, end, visual_description, asr_text

        Returns:
            Formatted text string for embedding
        """
        start_str = self._format_timestamp(result["start"])
        end_str = self._format_timestamp(result["end"])

        lines = [f"[{start_str}–{end_str}]"]

        if result.get("asr_text"):
            # Audio + Visual format
            lines.append(f"Instruction: {result['asr_text'].strip()}")
            lines.append(f"Visual: {result['visual_description'].strip()}")
        else:
            # Visual-only format
            lines.append(result["visual_description"].strip())

        return "\n".join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds as MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted string like "02:15"
        """
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def _build_metadata(
        self,
        result: Dict[str, Any],
        media_id: str,
        audio_usability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build ChromaDB metadata for fused chunk.

        Args:
            result: VLM result dict
            media_id: Media identifier
            audio_usability: Audio usability analysis dict

        Returns:
            Metadata dict for ChromaDB
        """
        has_audio = result.get("asr_text") is not None

        if has_audio:
            modality = "audio_visual"
            source_models = "Whisper,SmolVLM2"
        else:
            modality = "visual"
            source_models = "SmolVLM2"

        return {
            "media_id": media_id,
            "start_time": result["start"],
            "end_time": result["end"],
            "modality": modality,
            "audio_usable": audio_usability.get("audio_usable", False),
            "audio_classification": audio_usability.get("classification", "unknown"),
            "source_models": source_models,
            "frame_count": result.get("frame_count", 0),
        }
