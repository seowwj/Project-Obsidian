import sys
import os
import sonora.asgi
import grpc
# Add path to find app modules
sys.path.append('.') 

import app.service_pb2_grpc as service_pb2_grpc
from app.server import ObsidianService

print("Creating App...")
app = sonora.asgi.grpcASGI(enable_cors=False)

print("Adding Servicer...")
service_pb2_grpc.add_ObsidianServiceServicer_to_server(ObsidianService(), app)

print("Inspecting App...")
print(f"Dir: {dir(app)}")

if hasattr(app, '_rsvp_handlers'):
    print(f"_rsvp_handlers: {list(app._rsvp_handlers.keys())}")
elif hasattr(app, '_rpc_handlers'):
    print(f"_rpc_handlers: {list(app._rpc_handlers.keys())}")
else:
    print("Could not find handlers dict")

# Check if generic handlers are stored
if hasattr(app, 'add_generic_rpc_handlers'):
    # Check private storage if possible
    # Usually it's in _rpc_handlers for sonora
    pass
