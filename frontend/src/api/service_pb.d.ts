import * as jspb from 'google-protobuf'



export class UploadRequest extends jspb.Message {
  getFilePath(): string;
  setFilePath(value: string): UploadRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): UploadRequest.AsObject;
  static toObject(includeInstance: boolean, msg: UploadRequest): UploadRequest.AsObject;
  static serializeBinaryToWriter(message: UploadRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): UploadRequest;
  static deserializeBinaryFromReader(message: UploadRequest, reader: jspb.BinaryReader): UploadRequest;
}

export namespace UploadRequest {
  export type AsObject = {
    filePath: string,
  }
}

export class UploadResponse extends jspb.Message {
  getVideoId(): string;
  setVideoId(value: string): UploadResponse;

  getStatus(): string;
  setStatus(value: string): UploadResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): UploadResponse.AsObject;
  static toObject(includeInstance: boolean, msg: UploadResponse): UploadResponse.AsObject;
  static serializeBinaryToWriter(message: UploadResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): UploadResponse;
  static deserializeBinaryFromReader(message: UploadResponse, reader: jspb.BinaryReader): UploadResponse;
}

export namespace UploadResponse {
  export type AsObject = {
    videoId: string,
    status: string,
  }
}

export class ChatRequest extends jspb.Message {
  getSessionId(): string;
  setSessionId(value: string): ChatRequest;

  getVideoId(): string;
  setVideoId(value: string): ChatRequest;

  getMessage(): string;
  setMessage(value: string): ChatRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ChatRequest.AsObject;
  static toObject(includeInstance: boolean, msg: ChatRequest): ChatRequest.AsObject;
  static serializeBinaryToWriter(message: ChatRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ChatRequest;
  static deserializeBinaryFromReader(message: ChatRequest, reader: jspb.BinaryReader): ChatRequest;
}

export namespace ChatRequest {
  export type AsObject = {
    sessionId: string,
    videoId: string,
    message: string,
  }
}

export class ChatResponse extends jspb.Message {
  getContent(): string;
  setContent(value: string): ChatResponse;

  getType(): string;
  setType(value: string): ChatResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ChatResponse.AsObject;
  static toObject(includeInstance: boolean, msg: ChatResponse): ChatResponse.AsObject;
  static serializeBinaryToWriter(message: ChatResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ChatResponse;
  static deserializeBinaryFromReader(message: ChatResponse, reader: jspb.BinaryReader): ChatResponse;
}

export namespace ChatResponse {
  export type AsObject = {
    content: string,
    type: string,
  }
}

export class GetHistoryRequest extends jspb.Message {
  getSessionId(): string;
  setSessionId(value: string): GetHistoryRequest;

  getVideoId(): string;
  setVideoId(value: string): GetHistoryRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): GetHistoryRequest.AsObject;
  static toObject(includeInstance: boolean, msg: GetHistoryRequest): GetHistoryRequest.AsObject;
  static serializeBinaryToWriter(message: GetHistoryRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): GetHistoryRequest;
  static deserializeBinaryFromReader(message: GetHistoryRequest, reader: jspb.BinaryReader): GetHistoryRequest;
}

export namespace GetHistoryRequest {
  export type AsObject = {
    sessionId: string,
    videoId: string,
  }
}

export class GetHistoryResponse extends jspb.Message {
  getMessagesList(): Array<ChatMessage>;
  setMessagesList(value: Array<ChatMessage>): GetHistoryResponse;
  clearMessagesList(): GetHistoryResponse;
  addMessages(value?: ChatMessage, index?: number): ChatMessage;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): GetHistoryResponse.AsObject;
  static toObject(includeInstance: boolean, msg: GetHistoryResponse): GetHistoryResponse.AsObject;
  static serializeBinaryToWriter(message: GetHistoryResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): GetHistoryResponse;
  static deserializeBinaryFromReader(message: GetHistoryResponse, reader: jspb.BinaryReader): GetHistoryResponse;
}

export namespace GetHistoryResponse {
  export type AsObject = {
    messagesList: Array<ChatMessage.AsObject>,
  }
}

export class ChatMessage extends jspb.Message {
  getRole(): string;
  setRole(value: string): ChatMessage;

  getContent(): string;
  setContent(value: string): ChatMessage;

  getTimestamp(): string;
  setTimestamp(value: string): ChatMessage;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ChatMessage.AsObject;
  static toObject(includeInstance: boolean, msg: ChatMessage): ChatMessage.AsObject;
  static serializeBinaryToWriter(message: ChatMessage, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ChatMessage;
  static deserializeBinaryFromReader(message: ChatMessage, reader: jspb.BinaryReader): ChatMessage;
}

export namespace ChatMessage {
  export type AsObject = {
    role: string,
    content: string,
    timestamp: string,
  }
}

export class ListVideosRequest extends jspb.Message {
  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ListVideosRequest.AsObject;
  static toObject(includeInstance: boolean, msg: ListVideosRequest): ListVideosRequest.AsObject;
  static serializeBinaryToWriter(message: ListVideosRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ListVideosRequest;
  static deserializeBinaryFromReader(message: ListVideosRequest, reader: jspb.BinaryReader): ListVideosRequest;
}

export namespace ListVideosRequest {
  export type AsObject = {
  }
}

export class ListVideosResponse extends jspb.Message {
  getVideosList(): Array<VideoMetadata>;
  setVideosList(value: Array<VideoMetadata>): ListVideosResponse;
  clearVideosList(): ListVideosResponse;
  addVideos(value?: VideoMetadata, index?: number): VideoMetadata;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ListVideosResponse.AsObject;
  static toObject(includeInstance: boolean, msg: ListVideosResponse): ListVideosResponse.AsObject;
  static serializeBinaryToWriter(message: ListVideosResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ListVideosResponse;
  static deserializeBinaryFromReader(message: ListVideosResponse, reader: jspb.BinaryReader): ListVideosResponse;
}

export namespace ListVideosResponse {
  export type AsObject = {
    videosList: Array<VideoMetadata.AsObject>,
  }
}

export class ClearHistoryRequest extends jspb.Message {
  getVideoId(): string;
  setVideoId(value: string): ClearHistoryRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ClearHistoryRequest.AsObject;
  static toObject(includeInstance: boolean, msg: ClearHistoryRequest): ClearHistoryRequest.AsObject;
  static serializeBinaryToWriter(message: ClearHistoryRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ClearHistoryRequest;
  static deserializeBinaryFromReader(message: ClearHistoryRequest, reader: jspb.BinaryReader): ClearHistoryRequest;
}

export namespace ClearHistoryRequest {
  export type AsObject = {
    videoId: string,
  }
}

export class ClearHistoryResponse extends jspb.Message {
  getSuccess(): boolean;
  setSuccess(value: boolean): ClearHistoryResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ClearHistoryResponse.AsObject;
  static toObject(includeInstance: boolean, msg: ClearHistoryResponse): ClearHistoryResponse.AsObject;
  static serializeBinaryToWriter(message: ClearHistoryResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ClearHistoryResponse;
  static deserializeBinaryFromReader(message: ClearHistoryResponse, reader: jspb.BinaryReader): ClearHistoryResponse;
}

export namespace ClearHistoryResponse {
  export type AsObject = {
    success: boolean,
  }
}

export class VideoMetadata extends jspb.Message {
  getId(): string;
  setId(value: string): VideoMetadata;

  getPath(): string;
  setPath(value: string): VideoMetadata;

  getStatus(): string;
  setStatus(value: string): VideoMetadata;

  getCreatedAt(): string;
  setCreatedAt(value: string): VideoMetadata;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): VideoMetadata.AsObject;
  static toObject(includeInstance: boolean, msg: VideoMetadata): VideoMetadata.AsObject;
  static serializeBinaryToWriter(message: VideoMetadata, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): VideoMetadata;
  static deserializeBinaryFromReader(message: VideoMetadata, reader: jspb.BinaryReader): VideoMetadata;
}

export namespace VideoMetadata {
  export type AsObject = {
    id: string,
    path: string,
    status: string,
    createdAt: string,
  }
}

export class SessionMetadata extends jspb.Message {
  getId(): string;
  setId(value: string): SessionMetadata;

  getTitle(): string;
  setTitle(value: string): SessionMetadata;

  getVideoId(): string;
  setVideoId(value: string): SessionMetadata;

  getCreatedAt(): string;
  setCreatedAt(value: string): SessionMetadata;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): SessionMetadata.AsObject;
  static toObject(includeInstance: boolean, msg: SessionMetadata): SessionMetadata.AsObject;
  static serializeBinaryToWriter(message: SessionMetadata, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): SessionMetadata;
  static deserializeBinaryFromReader(message: SessionMetadata, reader: jspb.BinaryReader): SessionMetadata;
}

export namespace SessionMetadata {
  export type AsObject = {
    id: string,
    title: string,
    videoId: string,
    createdAt: string,
  }
}

export class CreateSessionRequest extends jspb.Message {
  getVideoId(): string;
  setVideoId(value: string): CreateSessionRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): CreateSessionRequest.AsObject;
  static toObject(includeInstance: boolean, msg: CreateSessionRequest): CreateSessionRequest.AsObject;
  static serializeBinaryToWriter(message: CreateSessionRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): CreateSessionRequest;
  static deserializeBinaryFromReader(message: CreateSessionRequest, reader: jspb.BinaryReader): CreateSessionRequest;
}

export namespace CreateSessionRequest {
  export type AsObject = {
    videoId: string,
  }
}

export class CreateSessionResponse extends jspb.Message {
  getSession(): SessionMetadata;
  setSession(value?: SessionMetadata): CreateSessionResponse;
  hasSession(): boolean;
  clearSession(): CreateSessionResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): CreateSessionResponse.AsObject;
  static toObject(includeInstance: boolean, msg: CreateSessionResponse): CreateSessionResponse.AsObject;
  static serializeBinaryToWriter(message: CreateSessionResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): CreateSessionResponse;
  static deserializeBinaryFromReader(message: CreateSessionResponse, reader: jspb.BinaryReader): CreateSessionResponse;
}

export namespace CreateSessionResponse {
  export type AsObject = {
    session?: SessionMetadata.AsObject,
  }
}

export class ListSessionsRequest extends jspb.Message {
  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ListSessionsRequest.AsObject;
  static toObject(includeInstance: boolean, msg: ListSessionsRequest): ListSessionsRequest.AsObject;
  static serializeBinaryToWriter(message: ListSessionsRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ListSessionsRequest;
  static deserializeBinaryFromReader(message: ListSessionsRequest, reader: jspb.BinaryReader): ListSessionsRequest;
}

export namespace ListSessionsRequest {
  export type AsObject = {
  }
}

export class ListSessionsResponse extends jspb.Message {
  getSessionsList(): Array<SessionMetadata>;
  setSessionsList(value: Array<SessionMetadata>): ListSessionsResponse;
  clearSessionsList(): ListSessionsResponse;
  addSessions(value?: SessionMetadata, index?: number): SessionMetadata;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): ListSessionsResponse.AsObject;
  static toObject(includeInstance: boolean, msg: ListSessionsResponse): ListSessionsResponse.AsObject;
  static serializeBinaryToWriter(message: ListSessionsResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): ListSessionsResponse;
  static deserializeBinaryFromReader(message: ListSessionsResponse, reader: jspb.BinaryReader): ListSessionsResponse;
}

export namespace ListSessionsResponse {
  export type AsObject = {
    sessionsList: Array<SessionMetadata.AsObject>,
  }
}

export class DeleteSessionRequest extends jspb.Message {
  getSessionId(): string;
  setSessionId(value: string): DeleteSessionRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): DeleteSessionRequest.AsObject;
  static toObject(includeInstance: boolean, msg: DeleteSessionRequest): DeleteSessionRequest.AsObject;
  static serializeBinaryToWriter(message: DeleteSessionRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): DeleteSessionRequest;
  static deserializeBinaryFromReader(message: DeleteSessionRequest, reader: jspb.BinaryReader): DeleteSessionRequest;
}

export namespace DeleteSessionRequest {
  export type AsObject = {
    sessionId: string,
  }
}

export class DeleteSessionResponse extends jspb.Message {
  getSuccess(): boolean;
  setSuccess(value: boolean): DeleteSessionResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): DeleteSessionResponse.AsObject;
  static toObject(includeInstance: boolean, msg: DeleteSessionResponse): DeleteSessionResponse.AsObject;
  static serializeBinaryToWriter(message: DeleteSessionResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): DeleteSessionResponse;
  static deserializeBinaryFromReader(message: DeleteSessionResponse, reader: jspb.BinaryReader): DeleteSessionResponse;
}

export namespace DeleteSessionResponse {
  export type AsObject = {
    success: boolean,
  }
}


export class RenameSessionRequest extends jspb.Message {
  getSessionId(): string;
  setSessionId(value: string): RenameSessionRequest;

  getNewTitle(): string;
  setNewTitle(value: string): RenameSessionRequest;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): RenameSessionRequest.AsObject;
  static toObject(includeInstance: boolean, msg: RenameSessionRequest): RenameSessionRequest.AsObject;
  static serializeBinaryToWriter(message: RenameSessionRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): RenameSessionRequest;
  static deserializeBinaryFromReader(message: RenameSessionRequest, reader: jspb.BinaryReader): RenameSessionRequest;
}

export namespace RenameSessionRequest {
  export type AsObject = {
    sessionId: string,
    newTitle: string,
  }
}


export class RenameSessionResponse extends jspb.Message {
  getSuccess(): boolean;
  setSuccess(value: boolean): RenameSessionResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): RenameSessionResponse.AsObject;
  static toObject(includeInstance: boolean, msg: RenameSessionResponse): RenameSessionResponse.AsObject;
  static serializeBinaryToWriter(message: RenameSessionResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): RenameSessionResponse;
  static deserializeBinaryFromReader(message: RenameSessionResponse, reader: jspb.BinaryReader): RenameSessionResponse;
}

export namespace RenameSessionResponse {
  export type AsObject = {
    success: boolean,
  }
}

export class GetStatusRequest extends jspb.Message {
  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): GetStatusRequest.AsObject;
  static toObject(includeInstance: boolean, msg: GetStatusRequest): GetStatusRequest.AsObject;
  static serializeBinaryToWriter(message: GetStatusRequest, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): GetStatusRequest;
  static deserializeBinaryFromReader(message: GetStatusRequest, reader: jspb.BinaryReader): GetStatusRequest;
}

export namespace GetStatusRequest {
  export type AsObject = {
  }
}

export class GetStatusResponse extends jspb.Message {
  getModelLoaded(): boolean;
  setModelLoaded(value: boolean): GetStatusResponse;

  serializeBinary(): Uint8Array;
  toObject(includeInstance?: boolean): GetStatusResponse.AsObject;
  static toObject(includeInstance: boolean, msg: GetStatusResponse): GetStatusResponse.AsObject;
  static serializeBinaryToWriter(message: GetStatusResponse, writer: jspb.BinaryWriter): void;
  static deserializeBinary(bytes: Uint8Array): GetStatusResponse;
  static deserializeBinaryFromReader(message: GetStatusResponse, reader: jspb.BinaryReader): GetStatusResponse;
}

export namespace GetStatusResponse {
  export type AsObject = {
    modelLoaded: boolean,
  }
}
