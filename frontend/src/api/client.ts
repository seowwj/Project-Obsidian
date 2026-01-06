import './service_grpc_web_pb';
import './service_pb';

// Access the client from the global scope (populated by the side-effects of the imports above)
// This bypasses module interop issues with generated CommonJS code
const { ObsidianServiceClient } = (window as any).proto.obsidian;
const { ChatRequest, UploadRequest, GetHistoryRequest } = (window as any).proto.obsidian;

// gRPC-Web Client
// Using localhost:8080 where Sonora is listening
const client = new ObsidianServiceClient('http://localhost:8080');

export const uploadVideo = (filePath: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    const request = new UploadRequest();
    request.setFilePath(filePath);

    client.uploadVideo(request, {}, (err, response) => {
      if (err) {
        console.error("Upload error:", err);
        reject(err.message);
      } else {
        resolve(response.getVideoId());
      }
    });
  });
};

export const getHistory = (videoId: string): Promise<any[]> => {
  return new Promise((resolve, reject) => {
    const request = new GetHistoryRequest();
    request.setVideoId(videoId);

    client.getHistory(request, {}, (err, response) => {
      if (err) {
        reject(err.message);
      } else {
        resolve(response.getMessagesList().map(msg => ({
          role: msg.getRole(),
          content: msg.getContent(),
          timestamp: msg.getTimestamp()
        })));
      }
    });
  });
};

export const chatStream = (videoId: string, message: string, onMessage: (text: string) => void, onEnd: () => void, onError: (err: string) => void) => {
  const request = new ChatRequest();
  request.setVideoId(videoId);
  request.setMessage(message);

  const stream = client.chat(request, {});

  stream.on('data', (response) => {
    // Only handle 'text' type for now
    if (response.getType() === 'text') {
      onMessage(response.getContent());
    }
  });

  stream.on('end', () => {
    onEnd();
  });

  stream.on('error', (err) => {
    console.error("Stream error:", err);
    onError(err.message);
  });

  return stream;
};
