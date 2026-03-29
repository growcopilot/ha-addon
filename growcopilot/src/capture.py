"""Capture loop — takes snapshots from mapped HA cameras and uploads to GrowCopilot."""
import asyncio
import logging
import time
from typing import Any
from src.ha_client import HASupervisorClient
from src.gc_client import GrowCopilotClient

logger = logging.getLogger("growcopilot.capture")
LOOP_TICK_SEC = 10

class CaptureLoop:
    def __init__(self, gc_client: GrowCopilotClient) -> None:
        self.gc = gc_client
        self.ha = HASupervisorClient()
        self.targets: dict[str, dict[str, Any]] = {}
        self._last_capture: dict[str, float] = {}

    def update_targets(self, targets: dict[str, dict[str, Any]]) -> None:
        self.targets = dict(targets)
        stale = set(self._last_capture) - set(self.targets)
        for key in stale:
            del self._last_capture[key]

    async def run(self) -> None:
        while True:
            now = time.time()
            for entity_id, target in self.targets.items():
                interval = target.get("intervalSec", 900)
                last = self._last_capture.get(entity_id, 0)
                if now - last >= interval:
                    await self._capture_and_upload(entity_id, target["growSpaceId"])
                    self._last_capture[entity_id] = now
            await asyncio.sleep(LOOP_TICK_SEC)

    async def _capture_and_upload(self, entity_id: str, grow_space_id: str) -> None:
        try:
            image_data = await self.ha.get_camera_snapshot(entity_id)
            if not image_data:
                logger.warning("Empty snapshot for %s", entity_id)
                return
            await self.gc.upload_snapshot(image_data, grow_space_id, entity_id)
        except Exception:
            logger.exception("Capture failed for %s", entity_id)
