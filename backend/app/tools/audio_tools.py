from langchain_core.tools import tool
from ..vector_store import VectorStore
import logging

logger = logging.getLogger(__name__)

# Initialize VectorStore lazily or globally? 
# Better to initialize inside or pass it. But tools usually need to be standalone.
# We'll initialize a new client instance for simplicity or rely on a singleton if we had one.
# For now, let's instantiate.

@tool
def get_whole_transcript(media_id: str) -> str:
    """
    Retrieves the full transcript for a given media_id from the Vector Store.
    Useful when you need the complete text to summarize or answer questions about the whole file.
    """
    logger.info(f"Tool execution: get_whole_transcript for {media_id}")
    store = VectorStore(collection_name="asr_segments")
    
    # Fetch all segments for this media_id
    # We can't easily "get all", but we can query by metadata
    results = store.get_by_metadata(where={"media_id": media_id})
    
    if not results or not results['ids']:
        return "No transcript found for this media file."
    
    # Reconstruct and sort
    segments = []
    ids = results['ids']
    metadatas = results['metadatas']
    documents = results['documents']
    
    for i, meta in enumerate(metadatas):
        segments.append({
            "start": meta.get("start", 0),
            "text": documents[i]
        })
        
    # Sort by start time
    segments.sort(key=lambda x: x["start"])
    
    full_text = " ".join([seg["text"] for seg in segments])
    return f"Full Transcript:\n{full_text}"

@tool
def export_transcript_srt(media_id: str) -> str:
    """
    Exports the transcript for a given media_id in SRT format.
    Useful when the user asks to export or see the SRT file.
    """
    logger.info(f"Tool execution: export_transcript_srt for {media_id}")
    store = VectorStore(collection_name="asr_segments")
    
    results = store.get_by_metadata(where={"media_id": media_id})
    
    if not results or not results['ids']:
        return "No transcript found for this media file."
        
    segments = []
    ids = results['ids']
    metadatas = results['metadatas']
    documents = results['documents']
    
    for i, meta in enumerate(metadatas):
        segments.append({
            "start": meta.get("start", 0),
            "end": meta.get("end", 0),
            "text": documents[i]
        })
    
    segments.sort(key=lambda x: x["start"])
    
    def format_timestamp(seconds):
        # SRT format: HH:MM:SS,mmm
        millis = int((seconds % 1) * 1000)
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

    srt_output = ""
    for idx, seg in enumerate(segments):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"].strip()
        
        srt_output += f"{idx+1}\n{start} --> {end}\n{text}\n\n"
        
    return srt_output
