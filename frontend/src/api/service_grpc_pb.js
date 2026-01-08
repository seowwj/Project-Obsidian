// GENERATED CODE -- DO NOT EDIT!

'use strict';
var grpc = require('@grpc/grpc-js');
var service_pb = require('./service_pb.js');

function serialize_obsidian_ChatRequest(arg) {
  if (!(arg instanceof service_pb.ChatRequest)) {
    throw new Error('Expected argument of type obsidian.ChatRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_ChatRequest(buffer_arg) {
  return service_pb.ChatRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_ChatResponse(arg) {
  if (!(arg instanceof service_pb.ChatResponse)) {
    throw new Error('Expected argument of type obsidian.ChatResponse');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_ChatResponse(buffer_arg) {
  return service_pb.ChatResponse.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_CreateSessionRequest(arg) {
  if (!(arg instanceof service_pb.CreateSessionRequest)) {
    throw new Error('Expected argument of type obsidian.CreateSessionRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_CreateSessionRequest(buffer_arg) {
  return service_pb.CreateSessionRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_CreateSessionResponse(arg) {
  if (!(arg instanceof service_pb.CreateSessionResponse)) {
    throw new Error('Expected argument of type obsidian.CreateSessionResponse');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_CreateSessionResponse(buffer_arg) {
  return service_pb.CreateSessionResponse.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_DeleteSessionRequest(arg) {
  if (!(arg instanceof service_pb.DeleteSessionRequest)) {
    throw new Error('Expected argument of type obsidian.DeleteSessionRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_DeleteSessionRequest(buffer_arg) {
  return service_pb.DeleteSessionRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_DeleteSessionResponse(arg) {
  if (!(arg instanceof service_pb.DeleteSessionResponse)) {
    throw new Error('Expected argument of type obsidian.DeleteSessionResponse');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_DeleteSessionResponse(buffer_arg) {
  return service_pb.DeleteSessionResponse.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_GetHistoryRequest(arg) {
  if (!(arg instanceof service_pb.GetHistoryRequest)) {
    throw new Error('Expected argument of type obsidian.GetHistoryRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_GetHistoryRequest(buffer_arg) {
  return service_pb.GetHistoryRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_GetHistoryResponse(arg) {
  if (!(arg instanceof service_pb.GetHistoryResponse)) {
    throw new Error('Expected argument of type obsidian.GetHistoryResponse');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_GetHistoryResponse(buffer_arg) {
  return service_pb.GetHistoryResponse.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_ListSessionsRequest(arg) {
  if (!(arg instanceof service_pb.ListSessionsRequest)) {
    throw new Error('Expected argument of type obsidian.ListSessionsRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_ListSessionsRequest(buffer_arg) {
  return service_pb.ListSessionsRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_ListSessionsResponse(arg) {
  if (!(arg instanceof service_pb.ListSessionsResponse)) {
    throw new Error('Expected argument of type obsidian.ListSessionsResponse');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_ListSessionsResponse(buffer_arg) {
  return service_pb.ListSessionsResponse.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_ListVideosRequest(arg) {
  if (!(arg instanceof service_pb.ListVideosRequest)) {
    throw new Error('Expected argument of type obsidian.ListVideosRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_ListVideosRequest(buffer_arg) {
  return service_pb.ListVideosRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_ListVideosResponse(arg) {
  if (!(arg instanceof service_pb.ListVideosResponse)) {
    throw new Error('Expected argument of type obsidian.ListVideosResponse');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_ListVideosResponse(buffer_arg) {
  return service_pb.ListVideosResponse.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_UploadRequest(arg) {
  if (!(arg instanceof service_pb.UploadRequest)) {
    throw new Error('Expected argument of type obsidian.UploadRequest');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_UploadRequest(buffer_arg) {
  return service_pb.UploadRequest.deserializeBinary(new Uint8Array(buffer_arg));
}

function serialize_obsidian_UploadResponse(arg) {
  if (!(arg instanceof service_pb.UploadResponse)) {
    throw new Error('Expected argument of type obsidian.UploadResponse');
  }
  return Buffer.from(arg.serializeBinary());
}

function deserialize_obsidian_UploadResponse(buffer_arg) {
  return service_pb.UploadResponse.deserializeBinary(new Uint8Array(buffer_arg));
}


var ObsidianServiceService = exports.ObsidianServiceService = {
  // Uploads a video for processing. Returns the video ID.
uploadVideo: {
    path: '/obsidian.ObsidianService/UploadVideo',
    requestStream: false,
    responseStream: false,
    requestType: service_pb.UploadRequest,
    responseType: service_pb.UploadResponse,
    requestSerialize: serialize_obsidian_UploadRequest,
    requestDeserialize: deserialize_obsidian_UploadRequest,
    responseSerialize: serialize_obsidian_UploadResponse,
    responseDeserialize: deserialize_obsidian_UploadResponse,
  },
  // Creates a new chat session (optionally linked to a video).
createSession: {
    path: '/obsidian.ObsidianService/CreateSession',
    requestStream: false,
    responseStream: false,
    requestType: service_pb.CreateSessionRequest,
    responseType: service_pb.CreateSessionResponse,
    requestSerialize: serialize_obsidian_CreateSessionRequest,
    requestDeserialize: deserialize_obsidian_CreateSessionRequest,
    responseSerialize: serialize_obsidian_CreateSessionResponse,
    responseDeserialize: deserialize_obsidian_CreateSessionResponse,
  },
  // Sends a chat message and receives a streaming response.
chat: {
    path: '/obsidian.ObsidianService/Chat',
    requestStream: false,
    responseStream: true,
    requestType: service_pb.ChatRequest,
    responseType: service_pb.ChatResponse,
    requestSerialize: serialize_obsidian_ChatRequest,
    requestDeserialize: deserialize_obsidian_ChatRequest,
    responseSerialize: serialize_obsidian_ChatResponse,
    responseDeserialize: deserialize_obsidian_ChatResponse,
  },
  // Retrieves chat history for a session.
getHistory: {
    path: '/obsidian.ObsidianService/GetHistory',
    requestStream: false,
    responseStream: false,
    requestType: service_pb.GetHistoryRequest,
    responseType: service_pb.GetHistoryResponse,
    requestSerialize: serialize_obsidian_GetHistoryRequest,
    requestDeserialize: deserialize_obsidian_GetHistoryRequest,
    responseSerialize: serialize_obsidian_GetHistoryResponse,
    responseDeserialize: deserialize_obsidian_GetHistoryResponse,
  },
  // List all sessions.
listSessions: {
    path: '/obsidian.ObsidianService/ListSessions',
    requestStream: false,
    responseStream: false,
    requestType: service_pb.ListSessionsRequest,
    responseType: service_pb.ListSessionsResponse,
    requestSerialize: serialize_obsidian_ListSessionsRequest,
    requestDeserialize: deserialize_obsidian_ListSessionsRequest,
    responseSerialize: serialize_obsidian_ListSessionsResponse,
    responseDeserialize: deserialize_obsidian_ListSessionsResponse,
  },
  // List all uploaded videos (Legacy/Management).
listVideos: {
    path: '/obsidian.ObsidianService/ListVideos',
    requestStream: false,
    responseStream: false,
    requestType: service_pb.ListVideosRequest,
    responseType: service_pb.ListVideosResponse,
    requestSerialize: serialize_obsidian_ListVideosRequest,
    requestDeserialize: deserialize_obsidian_ListVideosRequest,
    responseSerialize: serialize_obsidian_ListVideosResponse,
    responseDeserialize: deserialize_obsidian_ListVideosResponse,
  },
  // Delete a session.
deleteSession: {
    path: '/obsidian.ObsidianService/DeleteSession',
    requestStream: false,
    responseStream: false,
    requestType: service_pb.DeleteSessionRequest,
    responseType: service_pb.DeleteSessionResponse,
    requestSerialize: serialize_obsidian_DeleteSessionRequest,
    requestDeserialize: deserialize_obsidian_DeleteSessionRequest,
    responseSerialize: serialize_obsidian_DeleteSessionResponse,
    responseDeserialize: deserialize_obsidian_DeleteSessionResponse,
  },
};

exports.ObsidianServiceClient = grpc.makeGenericClientConstructor(ObsidianServiceService, 'ObsidianService');
