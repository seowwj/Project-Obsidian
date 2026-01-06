import * as grpcWeb from 'grpc-web';

import * as service_pb from './service_pb'; // proto import: "service.proto"


export class ObsidianServiceClient {
  constructor (hostname: string,
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

}

export class ObsidianServicePromiseClient {
  constructor (hostname: string,
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

}

