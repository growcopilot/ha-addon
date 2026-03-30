"""Config sync — polls GrowCopilot for entity mappings and capture intervals."""
import asyncio
import logging
from typing import TYPE_CHECKING
from src.gc_client import GrowCopilotClient

if TYPE_CHECKING:
    from src.capture import CaptureLoop
    from src.sensor_push import SensorPushLoop

logger = logging.getLogger("growcopilot.config_sync")
CONFIG_POLL_INTERVAL_SEC = 60

class ConfigSyncLoop:
    def __init__(
        self,
        gc_client: GrowCopilotClient,
        capture_loop: "CaptureLoop",
        sensor_push_loop: "SensorPushLoop | None" = None,
    ) -> None:
        self.gc = gc_client
        self.capture = capture_loop
        self.sensor_push = sensor_push_loop

    async def run(self) -> None:
        while True:
            config = await self.gc.get_device_config()
            entities = config.get("entities", [])

            camera_targets: dict[str, dict] = {}
            sensor_targets: dict[str, dict] = {}

            for entity in entities:
                eid = entity.get("entityId", "")
                space_id = entity.get("growSpaceId")
                if not space_id:
                    continue

                if entity.get("entityType") == "camera":
                    interval = 900
                    cfg = entity.get("config")
                    if isinstance(cfg, dict):
                        interval = cfg.get("captureIntervalSec", 900)
                    camera_targets[eid] = {"growSpaceId": space_id, "intervalSec": interval}
                elif entity.get("entityType") == "sensor":
                    sensor_targets[eid] = {"growSpaceId": space_id}

            self.capture.update_targets(camera_targets)
            if self.sensor_push:
                self.sensor_push.update_targets(sensor_targets)

            logger.debug("Synced %d camera targets, %d sensor targets", len(camera_targets), len(sensor_targets))
            await asyncio.sleep(CONFIG_POLL_INTERVAL_SEC)
