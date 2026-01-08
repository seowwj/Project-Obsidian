import * as grpcWeb from 'grpc-web';

import * as service_pb from './service_pb'; // proto import: "service.proto"


export class ObsidianServiceClient {
  constructor(hostname: string,
    credentials?: null | { [index: string]: string; },
    options?: null | { [index: string]: any; });

  uploadVideo(
    request: service_pb.UploadRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
      response: service_pb.UploadResponse) => void
  ): grpcWeb.ClientReadableStream<service_pb.UploadResponse>;

  chat(
    request: service_pb.ChatRequest,
    metadata?: grpcWeb.Metadata
  ): grpcWeb.ClientReadableStream<service_pb.ChatResponse>;

  getHistory(
    request: service_pb.GetHistoryRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
      response: service_pb.GetHistoryResponse) => void
  ): grpcWeb.ClientReadableStream<service_pb.GetHistoryResponse>;

  createSession(
    request: service_pb.CreateSessionRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
      response: service_pb.CreateSessionResponse) => void
  ): grpcWeb.ClientReadableStream<service_pb.CreateSessionResponse>;

  listSessions(
    request: service_pb.ListSessionsRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
      response: service_pb.ListSessionsResponse) => void
  ): grpcWeb.ClientReadableStream<service_pb.ListSessionsResponse>;

  deleteSession(
    request: service_pb.DeleteSessionRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
      response: service_pb.DeleteSessionResponse) => void
  ): grpcWeb.ClientReadableStream<service_pb.DeleteSessionResponse>;

  renameSession(
    request: service_pb.RenameSessionRequest,
    metadata: grpcWeb.Metadata | undefined,
    callback: (err: grpcWeb.RpcError,
      response: service_pb.RenameSessionResponse) => void
  ): grpcWeb.ClientReadableStream<service_pb.RenameSessionResponse>;

}

export class ObsidianServicePromiseClient {
  constructor(hostname: string,
    credentials?: null | { [index: string]: string; },
    options?: null | { [index: string]: any; });

  uploadVideo(
    request: service_pb.UploadRequest,
    metadata?: grpcWeb.Metadata
  ): Promise<service_pb.UploadResponse>;

  chat(
    request: service_pb.ChatRequest,
    metadata?: grpcWeb.Metadata
  ): grpcWeb.ClientReadableStream<service_pb.ChatResponse>;

  getHistory(
    request: service_pb.GetHistoryRequest,
    metadata?: grpcWeb.Metadata
  ): Promise<service_pb.GetHistoryResponse>;

  renameSession(
    request: service_pb.RenameSessionRequest,
    metadata?: grpcWeb.Metadata
  ): Promise<service_pb.RenameSessionResponse>;

}

