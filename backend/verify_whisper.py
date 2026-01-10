import numpy as np
import soundfile as sf
import asyncio
import os
import logging
from app.orchestrator import AgentOrchestrator
from langchain_core.messages import HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def generate_sine_wave(filename, duration=3, samplerate=16000, freq=440):
    t = np.linspace(0, duration, int(samplerate * duration), False)
    audio = 0.5 * np.sin(2 * np.pi * freq * t)
    sf.write(filename, audio, samplerate)
    print(f"Generated {filename}")

async def run_test():

    test_with_dummy = False

    if test_with_dummy:
        audio_file = os.path.abspath("test_audio.wav")
        generate_sine_wave(audio_file)
    else:
        # Use test audio (with speech)
        current_path = os.path.dirname(os.path.abspath(__file__))
        audio_file = os.path.join(os.path.dirname(current_path), "test_media", "DarkDaysBeforeDocker.mp3")

    # 2. Initialize Orchestrator
    orchestrator = AgentOrchestrator()
    graph = orchestrator.graph

    # 3. Invoke with audio_path
    print("Invoking graph with audio_path...")
    input_state = {
        "messages": [],
        "audio_path": audio_file
    }

    # Run the graph (First run - Transcription)
    print("\n--- First Run (Transcription) ---")
    config = {"configurable": {"thread_id": "test_thread_1"}}
    result = await graph.ainvoke(input_state, config)

    segments = result.get("transcription_segments")
    if segments:
        print(f"Segments found: {len(segments)}")
        print(segments[:2])
    else:
        print("No transcription segments found!")

    # Run the graph (Second run - Cache Hit)
    print("\n--- Second Run (Cache Check) ---")
    config = {"configurable": {"thread_id": "test_thread_2"}}
    result_cache = await graph.ainvoke(input_state, config)
    segments_cache = result_cache.get("transcription_segments")
    print(f"Segments in cache run: {len(segments_cache) if segments_cache else 0}")

    # Clean up (only the dummy file)
    if os.path.exists(audio_file) and test_with_dummy:
        os.remove(audio_file)

if __name__ == "__main__":
    asyncio.run(run_test())
