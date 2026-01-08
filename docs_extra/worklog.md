## Work Log / Backlog / Scratchpad

### 2026-01-08 - v0.3
- Able to get preliminary frontend and backend to communicate. Major issue was with gRPC protos. (See [manual_proto_patches.md](manual_proto_patches.md) and [troubleshooting_proto.md](troubleshooting_proto.md))
- 🐞 BUG: GPU Generation will crash / terminate backend without issue. Reproduced (locally) with [sanity script](..\sanity_scripts\ov_genai.py) (Note there is no "End generation"). **CPU works without issue!**

![GPU Gen Issue](v0_3b-GPUIssues.png)
![CPU OK](v0_3a-CPUWorking.png)

- ⚠️ LIMITATION: No concept of memory. Current implementation is only QA for 1 turn.

![No memory context](v0_3c-NoMemoryContext.png)