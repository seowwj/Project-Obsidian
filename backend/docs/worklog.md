## Work Log / Backlog / Scratchpad

### 2026-01-09 - Fresh Start 🌱
- Simple chatbot with memory and streaming implemented using LangGraph.
- Using FastAPI (REST based) to communicate between frontend and backend. Future plan is to use ConnectRPC + Tauri.(replace `StreamingResponse` with a ConnectRPC handler.)

- ⚠️ LIMITATION: Chatbot memory is not persistent (no database). Future plan for drop in replacement in LangGraph (swap `MemorySaver` with `SqliteSaver`)

### 2026-01-08 - Fresh Start 🌱
- Removed all frontend code to focus on backend.
- Planned rearchitecture to use LangGraph to coordinate between all tool / agent use.

### 2026-01-08 - v0.4
- Added simple memory (simple sliding window of the past few conversations).
- Switch back to CPU generation (for now). Also switched back to larger SLM (Phi 3 mini).

![Memory](worklog_images/v0_4-Memory.png)

- 🔧 BUGFIX: Add "onComplete" for to identify whether LLM/SLM is still streaming output. Previously UI was stuck in "generating response" even if generation was complete.
- 🔧 BUGFIX: Fix removed video processing pipeline.

- ⚠️ LIMITATION: Current strategy for video understanding is inadequate. Currently brute forcing every 2nd frame analysis. Lacking in semantic understanding of video.

### 2026-01-08 - v0.3
- Able to get preliminary frontend and backend to communicate. Major issue was with gRPC protos. (See [manual_proto_patches.md](manual_proto_patches.md) and [troubleshooting_proto.md](troubleshooting_proto.md))
- 🐞 BUG: GPU Generation will crash / terminate backend without issue. Reproduced (locally) with [sanity script](..\sanity_scripts\ov_genai.py) (Note there is no "End generation"). **CPU works without issue!**

![GPU Gen Issue](worklog_images/v0_3b-GPUIssues.png)
![CPU OK](worklog_images/v0_3a-CPUWorking.png)

- ⚠️ LIMITATION: No concept of memory. Current implementation is only QA for 1 turn.

![No memory context](worklog_images/v0_3c-NoMemoryContext.png)