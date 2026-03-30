"""Entity discovery from Home Assistant."""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from src.ha_client import HASupervisorClient
from src.gc_client import GrowCopilotClient

logger = logging.getLogger("growcopilot.discovery")
SELECTED_ENTITIES_PATH = Path("/data/selected_entities.json")
DISCOVERY_INTERVAL_SEC = 600
GROW_SENSOR_CLASSES = {"temperature", "humidity", "illuminance", "moisture"}
CONTROLLABLE_DOMAINS = {"switch", "light", "fan"}

def filter_entities(states: list[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for state in states:
        eid: str = state.get("entity_id", "")
        attrs = state.get("attributes", {})
        friendly = attrs.get("friendly_name", eid)
        domain = eid.split(".")[0] if "." in eid else ""
        if domain == "camera":
            result.append({"entityId": eid, "entityType": "camera", "friendlyName": friendly})
        elif domain == "sensor":
            device_class = attrs.get("device_class", "")
            if device_class in GROW_SENSOR_CLASSES:
                result.append({"entityId": eid, "entityType": "sensor", "friendlyName": friendly})
        elif domain in CONTROLLABLE_DOMAINS:
            result.append({"entityId": eid, "entityType": domain, "friendlyName": friendly})
    return result

def load_selected_ids() -> set[str]:
    try:
        data = json.loads(SELECTED_ENTITIES_PATH.read_text())
        return set(data) if isinstance(data, list) else set()
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_selected_ids(ids: set[str]) -> None:
    SELECTED_ENTITIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    SELECTED_ENTITIES_PATH.write_text(json.dumps(sorted(ids)))

class DiscoveryLoop:
    def __init__(self, gc_client: GrowCopilotClient) -> None:
        self.ha = HASupervisorClient()
        self.gc = gc_client
        self.discovered: list[dict[str, str]] = []
        self.selected_ids: set[str] = load_selected_ids()

    async def discover_once(self) -> list[dict[str, str]]:
        try:
            states = await self.ha.get_states()
            self.discovered = filter_entities(states)
            logger.info("Discovered %d entities", len(self.discovered))
            return self.discovered
        except Exception:
            logger.exception("Discovery failed")
            return self.discovered

    async def push_selected(self) -> None:
        selected = [e for e in self.discovered if e["entityId"] in self.selected_ids]
        if selected:
            await self.gc.push_entities(selected)
            logger.info("Pushed %d selected entities", len(selected))

    def select_entities(self, entity_ids: list[str]) -> None:
        self.selected_ids = set(entity_ids)
        save_selected_ids(self.selected_ids)

    async def run(self) -> None:
        while True:
            await self.discover_once()
            await self.push_selected()
            await asyncio.sleep(DISCOVERY_INTERVAL_SEC)
