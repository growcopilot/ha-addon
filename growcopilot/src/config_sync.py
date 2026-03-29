"""Config sync — polls GrowCopilot for entity mappings and capture intervals."""
import asyncio
import logging
from typing import TYPE_CHECKING
from src.gc_client import GrowCopilotClient

if TYPE_CHECKING:
    from src.capture import CaptureLoop

logger = logging.getLogger("growcopilot.config_sync")
CONFIG_POLL_INTERVAL_SEC = 60

class ConfigSyncLoop:
    def __init__(self, gc_client: GrowCopilotClient, capture_loop: "CaptureLoop") -> None:
        self.gc = gc_client
        self.capture = capture_loop

    async def run(self) -> None:
        while True:
            config = await self.gc.get_device_config()
            entities = config.get("entities", [])
            camera_targets: dict[str, dict] = {}
            for entity in entities:
                if entity.get("entityType") == "camera" and entity.get("growSpaceId"):
                    eid = entity["entityId"]
                    interval = 900
                    cfg = entity.get("config")
                    if isinstance(cfg, dict):
                        interval = cfg.get("captureIntervalSec", 900)
                    camera_targets[eid] = {"growSpaceId": entity["growSpaceId"], "intervalSec": interval}
            self.capture.update_targets(camera_targets)
            logger.debug("Synced %d camera targets", len(camera_targets))
            await asyncio.sleep(CONFIG_POLL_INTERVAL_SEC)
