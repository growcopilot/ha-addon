"""Home Assistant Supervisor API client."""
import os
import logging
from typing import Any
import aiohttp

logger = logging.getLogger("growcopilot.ha_client")
SUPERVISOR_URL = "http://supervisor"
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")

class HASupervisorClient:
    def __init__(self) -> None:
        self._headers = {"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}

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
