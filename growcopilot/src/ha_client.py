"""Home Assistant Supervisor API client."""
from __future__ import annotations
import os
import logging
from typing import Any, Optional
import aiohttp

logger = logging.getLogger("growcopilot.ha_client")
SUPERVISOR_URL = "http://supervisor"


class HASupervisorClient:
    def __init__(self) -> None:
        token = os.environ.get("SUPERVISOR_TOKEN", "")
        if not token:
            logger.warning("SUPERVISOR_TOKEN not set — Supervisor API calls will fail")
        else:
            logger.info("SUPERVISOR_TOKEN found (%d chars)", len(token))
        self._headers = {"Authorization": f"Bearer {token}"}

    async def get_states(self) -> list[dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SUPERVISOR_URL}/core/api/states", headers=self._headers) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_camera_snapshot(self, entity_id: str) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SUPERVISOR_URL}/core/api/camera_proxy/{entity_id}", headers=self._headers) as resp:
                resp.raise_for_status()
                return await resp.read()

    async def call_service(self, domain: str, service: str, entity_id: str, data: Optional[dict[str, Any]] = None) -> bool:
        """Call a Home Assistant service (e.g., switch/turn_on)."""
        payload: dict[str, Any] = {"entity_id": entity_id}
        if data:
            payload.update(data)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SUPERVISOR_URL}/core/api/services/{domain}/{service}",
                headers={**self._headers, "Content-Type": "application/json"},
                json=payload,
            ) as resp:
                return resp.ok

    async def get_entity_state(self, entity_id: str) -> Optional[dict[str, Any]]:
        """Get current state of a single entity."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SUPERVISOR_URL}/core/api/states/{entity_id}", headers=self._headers) as resp:
                if resp.ok:
                    return await resp.json()
                return None
