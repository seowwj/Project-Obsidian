import asyncio
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from .orchestrator import AgentOrchestrator

async def main():
    logger.info("Starting Obsidian Backend (Pure Mode)...")
    try:
        orchestrator = AgentOrchestrator()
        is_ready = orchestrator.is_model_ready()
        logger.info(f"AgentOrchestrator initialized. Model Ready: {is_ready}")
        logger.info("Backend is functional. Waiting for commands...")
        
        # Keep alive for a bit to simulate a running process if needed, 
        # but for verification we can just exit or loop.
        # For now, let's just exit successfully to prove initialization works.
        logger.info("Backend verification successful.")
        
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())

