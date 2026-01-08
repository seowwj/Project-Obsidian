// @ts-ignore
import * as service_grpc_web_pb from './service_grpc_web_pb';
// @ts-ignore
import * as service_pb from './service_pb';

// @ts-ignore
const service_grpc_web_pb_module = (service_grpc_web_pb as any).default || service_grpc_web_pb;
// @ts-ignore
const ObsidianServiceClient = service_grpc_web_pb_module.ObsidianServiceClient;

// @ts-ignore
let service_pb_module = (service_pb as any).default || service_pb;

// Fallback to global if import failed to find the classes (legacy google-protobuf support)
if (!service_pb_module || !service_pb_module.CreateSessionRequest) {
  const globalScope = typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : null) as any;
  if (globalScope && globalScope.proto && globalScope.proto.obsidian) {
    console.warn("Falling back to global proto.obsidian for messages");
    service_pb_module = globalScope.proto.obsidian;
  }
}

// @ts-ignore
const {
  CreateSessionRequest,
  ListSessionsRequest,
  DeleteSessionRequest,
  RenameSessionRequest,
  ChatRequest,
  GetHistoryRequest,
  UploadRequest,
  GetStatusRequest
} = service_pb_module;

// @ts-ignore
import type { ObsidianServiceClient as ProtoClient } from './service_grpc_web_pb';

// Singleton client instance
let clientInstance: ProtoClient | null = null;

const getClient = (): ProtoClient => {
  if (!clientInstance) {
    clientInstance = new ObsidianServiceClient('http://localhost:8080');
  }
  return clientInstance!;
};

// -- Session Management --

export const getStatus = (): Promise<boolean> => {
  return new Promise((resolve, reject) => {
    try {
      const client = getClient();
      const req = new GetStatusRequest();

      client.getStatus(req, {}, (err: any, response: any) => {
        if (err) {
          // If error (e.g. server not reachable), assume not loaded
          console.warn("GetStatus Error (assuming offline/loading):", err);
          resolve(false);
        } else {
          resolve(response.getModelLoaded());
        }
      });
    } catch (e) {
      console.error("GetStatus Exception:", e);
      resolve(false);
    }
  });
};

export const createSession = (videoId: string | null = null): Promise<string> => {
  return new Promise((resolve, reject) => {
    try {
      const client = getClient();
      const req = new CreateSessionRequest();
      if (videoId) {
        req.setVideoId(videoId);
      }

      client.createSession(req, {}, (err: any, response: any) => {
        if (err) {
          console.error("CreateSession Error:", err);
          reject(err);
        } else {
          const session = response.getSession();
          resolve(session.getId());
        }
      });
    } catch (e) {
      console.error("CreateSession Exception:", e);
      reject(e);
    }
  });
};

export const listSessions = (): Promise<any[]> => {
  return new Promise((resolve, reject) => {
    try {
      const client = getClient();
      const req = new ListSessionsRequest();

      client.listSessions(req, {}, (err: any, response: any) => {
        if (err) {
          console.error("ListSessions Error:", err);
          reject(err);
        } else {
          const sessionsList = response.getSessionsList();
          const sessions = sessionsList.map((s: any) => ({
            id: s.getId(),
            title: s.getTitle(),
            videoId: s.getVideoId(),
            createdAt: s.getCreatedAt(),
          }));
          resolve(sessions);
        }
      });
    } catch (e) {
      console.error("ListSessions Exception:", e);
      reject(e);
    }
  });
};

export const deleteSession = (sessionId: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    try {
      const client = getClient();
      const req = new DeleteSessionRequest();
      req.setSessionId(sessionId);

      client.deleteSession(req, {}, (err: any, response: any) => {
        if (err) {
          console.error("DeleteSession Error:", err);
          reject(err);
        } else {
          resolve();
        }
      });
    } catch (e) {
      console.error("DeleteSession Exception:", e);
      reject(e);
    }
  });
};

export const renameSession = (sessionId: string, newTitle: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    try {
      const client = getClient();
      const req = new RenameSessionRequest();
      req.setSessionId(sessionId);
      req.setNewTitle(newTitle);

      client.renameSession(req, {}, (err: any, response: any) => {
        if (err) {
          console.error("RenameSession Error:", err);
          reject(err);
        } else {
          resolve();
        }
      });
    } catch (e) {
      console.error("RenameSession Exception:", e);
      reject(e);
    }
  });
};

// -- Chat & History --

export const sendMessage = (sessionId: string, message: string, onMessage: (msg: string) => void, onError: (err: any) => void) => {
  try {
    const client = getClient();
    const req = new ChatRequest();
    req.setSessionId(sessionId);
    req.setMessage(message);

    const stream = client.chat(req, {});

    stream.on('data', (response: any) => {
      const type = response.getType();
      const content = response.getContent();
      if (type === 'error') {
        console.error("Chat Stream Error Message:", content);
        onError(content);
      } else {
        onMessage(content);
      }
    });

    stream.on('error', (err: any) => {
      console.error("Chat Stream Error:", err);
      onError(err);
    });

    stream.on('end', () => {
      // Stream ended
    });

    return () => stream.cancel();
  } catch (e) {
    console.error("SendMessage Exception:", e);
    onError(e);
    return () => { };
  }
};

export const getHistory = (sessionId: string): Promise<any[]> => {
  return new Promise((resolve, reject) => {
    try {
      const client = getClient();
      const req = new GetHistoryRequest();
      req.setSessionId(sessionId);

      client.getHistory(req, {}, (err: any, response: any) => {
        if (err) {
          console.error("GetHistory Error:", err);
          reject(err);
        } else {
          const msgsList = response.getMessagesList();
          const history = msgsList.map((m: any) => ({
            role: m.getRole(),
            content: m.getContent(),
            timestamp: m.getTimestamp()
          }));
          resolve(history);
        }
      });
    } catch (e) {
      console.error("GetHistory Exception:", e);
      reject(e);
    }
  });
};

// -- Video Management --

export const uploadVideo = (filePath: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    try {
      const client = getClient();
      const req = new UploadRequest();
      req.setFilePath(filePath);

      client.uploadVideo(req, {}, (err: any, response: any) => {
        if (err) {
          console.error("UploadVideo Error:", err);
          reject(err);
        } else {
          resolve(response.getVideoId());
        }
      });
    } catch (e) {
      console.error("UploadVideo Exception:", e);
      reject(e);
    }
  });
};
