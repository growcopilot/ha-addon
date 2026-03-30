"""GrowCopilot API client for the HA add-on."""
from __future__ import annotations

import io
import logging
from typing import Any, Optional
import aiohttp

logger = logging.getLogger("growcopilot.gc_client")
DEFAULT_API_BASE = "https://api.growcopilot.ai"

class GrowCopilotClient:
    def __init__(self, api_token: str = "", api_base_url: str = DEFAULT_API_BASE) -> None:
        self.api_token = api_token
        self.api_base_url = api_base_url.rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_token}"}

    def set_token(self, token: str) -> None:
        self.api_token = token

    async def validate_token(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/auth/token-info", headers=self._headers) as resp:
                    return resp.status == 200
        except Exception:
            logger.exception("Token validation failed")
            return False

    async def push_entities(self, entities: list[dict[str, str]]) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_base_url}/device/entities", headers={**self._headers, "Content-Type": "application/json"}, json={"entities": entities}) as resp:
                    if not resp.ok:
                        logger.warning("Entity push failed: %s", resp.status)
        except Exception:
            logger.exception("Entity push failed")

    async def get_device_config(self) -> dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/device/config", headers=self._headers) as resp:
                    if resp.ok:
                        return await resp.json()
                    return {"entities": []}
        except Exception:
            logger.exception("Config fetch failed")
            return {"entities": []}

    async def upload_snapshot(self, image_data: bytes, grow_space_id: str, entity_id: str) -> bool:
        try:
            data = aiohttp.FormData()
            data.add_field("image", io.BytesIO(image_data), filename=f"{entity_id}.jpg", content_type="image/jpeg")
            data.add_field("sourceType", "home-assistant")
            data.add_field("deviceName", entity_id)
            data.add_field("growSpaceId", grow_space_id)
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_base_url}/plant-image", headers=self._headers, data=data) as resp:
                    if resp.ok:
                        logger.info("Uploaded snapshot for %s", entity_id)
                        return True
                    logger.warning("Upload failed for %s: %s", entity_id, resp.status)
                    return False
        except Exception:
            logger.exception("Upload failed for %s", entity_id)
            return False

    async def send_heartbeat(self, device_name: str, source_type: str = "home-assistant", grow_space_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        try:
            payload: dict[str, Any] = {"name": device_name, "sourceType": source_type, "reportedConfig": {}}
            if grow_space_id:
                payload["growSpaceId"] = grow_space_id
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_base_url}/device/heartbeat", headers={**self._headers, "Content-Type": "application/json"}, json=payload) as resp:
                    if resp.ok:
                        return await resp.json()
                    return None
        except Exception:
            logger.exception("Heartbeat failed")
            return None

    async def push_sensor_readings(self, readings: list[dict[str, Any]]) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/device/sensor-readings",
                    headers={**self._headers, "Content-Type": "application/json"},
                    json={"readings": readings},
                ) as resp:
                    if not resp.ok:
                        logger.warning("Sensor push failed: %s", resp.status)
        except Exception:
            logger.exception("Sensor push failed")
