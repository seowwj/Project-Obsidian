import asyncio
import grpc
import sys
import os

# Add backend/app directory to sys.path to ensure imports work
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

import service_pb2
import service_pb2_grpc

async def run():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = service_pb2_grpc.ObsidianServiceStub(channel)
        
        print("1. Testing UploadVideo...")
        response = await stub.UploadVideo(service_pb2.UploadRequest(file_path="/path/to/video.mp4"))
        print(f"Server response: VideoID={response.video_id}, Status={response.status}")
        video_id = response.video_id

        print("\n2. Testing Chat...")
        async for chat_response in stub.Chat(service_pb2.ChatRequest(video_id=video_id, message="Hello Obsidian!")):
            print(f"Chat chunk: {chat_response.content} (Type: {chat_response.type})")

        print("\n3. Testing GetHistory...")
        history_response = await stub.GetHistory(service_pb2.GetHistoryRequest(video_id=video_id))
        for msg in history_response.messages:
            print(f"History: [{msg.role}] {msg.content}")

if __name__ == '__main__':
    asyncio.run(run())
