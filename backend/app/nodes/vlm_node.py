import logging
from typing import Dict, Any, List

from langchain_core.runnables import RunnableConfig

from .base_node import BaseNode
from ..state import AgentState
from ..vlm import VLMWrapper
from ..utils.frame_sampler import sample_frames


class VLMNode(BaseNode):
    """
    Process video chunks through SmolVLM2 for visual descriptions.
    
    Features:
    - Sequential processing (memory-constrained)
    - Audio-aligned prompts when ASR context available
    - Vision-only prompts for silent sequences
    
    Input state:
        processing_chunks: List[{start, end, asr_text}]
        video_path: str
        
    Output state:
        vlm_results: List[{start, end, visual_description, asr_text, frame_count}]
    """
    
    # Frame sampling parameters (tweak as necessary to avoid overflowing VLM context)
    FRAMES_PER_SECOND = 1.0
    MAX_FRAMES_PER_CHUNK = 8
    
    def __init__(self, model: VLMWrapper, frames_output_dir: str = None):
        """
        Initialize VLM Node.
        
        Args:
            frames_output_dir: Optional directory to store extracted frames
        """
        super().__init__(model=None, name="vlm_node")
        self.model = model
        self.frames_output_dir = frames_output_dir
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def __call__(self, state: AgentState, config: RunnableConfig = None) -> Dict[str, Any]:
        chunks = state.get("processing_chunks", [])
        video_path = state.get("video_path")
        
        if not chunks:
            self.logger.warning("No chunks to process, skipping VLM")
            return {"vlm_results": []}
        
        if not video_path:
            self.logger.warning("No video_path in state, skipping VLM")
            return {"vlm_results": []}

        vlm_results = []
        total_chunks = len(chunks)
        
        self.logger.info(f"Starting VLM processing for {total_chunks} chunks (sequential mode)")
        
        for i, chunk in enumerate(chunks):
            chunk_num = i + 1
            start = chunk.get("start", 0)
            end = chunk.get("end", 0)
            asr_text = chunk.get("asr_text")
            
            self.logger.info(f"Processing chunk {chunk_num}/{total_chunks}: [{start:.2f}-{end:.2f}s]")
            
            try:
                result = self._process_chunk(
                    video_path=video_path,
                    start=start,
                    end=end,
                    asr_text=asr_text
                )
                
                if result:
                    vlm_results.append(result)
                    self.logger.debug(f"Chunk {chunk_num} description: {result['visual_description'][:80]}...")
                    
            except Exception as e:
                self.logger.error(f"Failed to process chunk {chunk_num}: {e}")
                # Continue with next chunk instead of failing entirely
                continue
        
        self.logger.info(f"VLM processing complete: {len(vlm_results)}/{total_chunks} chunks processed")
        return {"vlm_results": vlm_results}
    
    def _process_chunk(
        self,
        video_path: str,
        start: float,
        end: float,
        asr_text: str = None
    ) -> Dict[str, Any]:
        """
        Process a single chunk through VLM.
        
        Args:
            video_path: Path to video file
            start: Chunk start time (seconds)
            end: Chunk end time (seconds)
            asr_text: Optional ASR context
            
        Returns:
            Dict with start, end, visual_description, asr_text, frame_count
        """
        # Sample frames for this chunk
        frames = sample_frames(
            video_path=video_path,
            start_time=start,
            end_time=end,
            fps=self.FRAMES_PER_SECOND,
            max_frames=self.MAX_FRAMES_PER_CHUNK,
            output_dir=self.frames_output_dir
        )
        
        if not frames:
            self.logger.warning(f"No frames extracted for chunk [{start:.2f}-{end:.2f}s]")
            return None
        
        frame_paths = [f["path"] for f in frames]
        
        # Generate visual description
        description = self.model.describe_frames(
            frame_paths=frame_paths,
            asr_context=asr_text
        )
        
        return {
            "start": start,
            "end": end,
            "visual_description": description,
            "asr_text": asr_text,
            "frame_count": len(frames)
        }
