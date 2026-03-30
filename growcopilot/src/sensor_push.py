"""Sensor push loop — reads sensor values from HA and pushes to GrowCopilot."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from src.ha_client import HASupervisorClient
from src.gc_client import GrowCopilotClient

logger = logging.getLogger("growcopilot.sensor_push")
SENSOR_PUSH_INTERVAL_SEC = 300  # 5 minutes


class SensorPushLoop:
    def __init__(self, gc_client: GrowCopilotClient) -> None:
        self.gc = gc_client
        self.ha = HASupervisorClient()
        self.targets: dict[str, dict[str, Any]] = {}

    def update_targets(self, targets: dict[str, dict[str, Any]]) -> None:
        """Update the sensor entity targets from config sync."""
        self.targets = dict(targets)

    async def run(self) -> None:
        while True:
            await asyncio.sleep(SENSOR_PUSH_INTERVAL_SEC)
            if not self.targets:
                continue
            await self._read_and_push()

    async def _read_and_push(self) -> None:
        try:
            states = await self.ha.get_states()
            state_map = {s["entity_id"]: s for s in states}

            readings = []
            now = datetime.now(timezone.utc).isoformat()

            for entity_id, target in self.targets.items():
                state = state_map.get(entity_id)
                if not state:
                    continue

                value_str = state.get("state", "")
                try:
                    value = float(value_str)
                except (ValueError, TypeError):
                    continue

                attrs = state.get("attributes", {})
                unit = attrs.get("unit_of_measurement", "")
                device_class = attrs.get("device_class", "unknown")

                readings.append({
                    "entityId": entity_id,
                    "entityType": device_class,
                    "value": value,
                    "unit": unit,
                    "recordedAt": now,
                })

            if readings:
                await self.gc.push_sensor_readings(readings)
                logger.info("Pushed %d sensor readings", len(readings))
        except Exception:
            logger.exception("Sensor push failed")
