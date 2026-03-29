"""Home Assistant Supervisor API client."""
import os
import logging
from typing import Any
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
