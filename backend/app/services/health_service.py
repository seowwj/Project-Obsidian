"""
ConnectRPC HealthService implementation.
Simple health check endpoint.
"""

import logging
import sys
from pathlib import Path

# Ensure gen folder is in path
_backend_dir = Path(__file__).parent.parent.parent
_gen_dir = _backend_dir / "gen"
if str(_gen_dir) not in sys.path:
    sys.path.insert(0, str(_gen_dir))

from connectrpc.request import RequestContext

from obsidian.v1.obsidian_pb2 import HealthCheckRequest, HealthCheckResponse
from obsidian.v1.obsidian_connect import HealthService

logger = logging.getLogger(__name__)


class ObsidianHealthService(HealthService):
    """
    ConnectRPC HealthService implementation.
    """

    async def check(
        self, request: HealthCheckRequest, ctx: RequestContext
    ) -> HealthCheckResponse:
        """
        Simple health check.
        
        Returns:
            HealthCheckResponse with status "ok"
        """
        return HealthCheckResponse(status="ok")
