"""Heartbeat loop — sends periodic heartbeat to GrowCopilot API."""
import asyncio
import logging
from src.gc_client import GrowCopilotClient

logger = logging.getLogger("growcopilot.heartbeat")
HEARTBEAT_INTERVAL_SEC = 120

class HeartbeatLoop:
    def __init__(self, gc_client: GrowCopilotClient, device_name: str = "Home Assistant") -> None:
        self.gc = gc_client
        self.device_name = device_name

    async def run_once(self) -> None:
        await self.gc.send_heartbeat(self.device_name)
        logger.debug("Heartbeat sent")

    async def run(self) -> None:
        while True:
            await self.run_once()
            await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)
