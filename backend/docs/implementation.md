# Backend Implementation Details: gRPC with Sonora

## Decision
We have decided to stick with **gRPC** utilizing **Sonora** to enable gRPC-Web support directly within the Python process.
**Reasoning**: This avoids the need for a separate sidecar proxy (Envoy), keeping the deployment architecture simple (single-binary/process potential) while preserving the strict type safety and contract enforcement of gRPC.

## Implementation Details

### 1. Server Wrapper (`server.py`)
We use `sonora.aio.SonoraWeb` to wrap the standard `grpc.aio.server`.
- **Standard gRPC**: Usually runs on HTTP/2.
- **Sonora**: Creates an HTTP/1.1 server that intercepts gRPC-Web requests, translates them, and forwards them to the gRPC handler.
- **Port**: We bind to port `8080`.

### 2. Dependency Management
Sonora is older and requires `urllib3<2.0`. We have pinned this in `requirements.txt`.
We are using `uv` for fast dependency resolution.

### 3. Frontend Generation
We use `protoc` with the `grpc-web` plugin to generate TypeScript stubs.
- `service_pb.js`: Message definitions.
- `service_grpc_web_pb.js`: Service client definitions.
