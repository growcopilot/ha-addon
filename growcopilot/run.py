"""GrowCopilot Home Assistant Add-on entry point."""
import asyncio
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("growcopilot")


async def main() -> None:
    from src.web.server import start_server
    from src.heartbeat import HeartbeatLoop
    from src.capture import CaptureLoop
    from src.discovery import DiscoveryLoop
    from src.config_sync import ConfigSyncLoop
    from src.gc_client import GrowCopilotClient

    api_token = os.environ.get("API_TOKEN", "")
    api_url = ""
    try:
        with open("/data/options.json") as f:
            options = json.load(f)
            api_token = api_token or options.get("api_token", "")
            api_url = options.get("api_url", "")
    except FileNotFoundError:
        pass

    gc_client = GrowCopilotClient(
        api_token=api_token,
        api_base_url=api_url or "https://api.growcopilot.ai",
    )
    ingress_port = int(os.environ.get("INGRESS_PORT", "8099"))

    heartbeat = HeartbeatLoop(gc_client)
    capture = CaptureLoop(gc_client)
    discovery = DiscoveryLoop(gc_client)
    config_sync = ConfigSyncLoop(gc_client, capture)

    tasks = [
        asyncio.create_task(start_server(ingress_port, gc_client, discovery)),
        asyncio.create_task(heartbeat.run()),
        asyncio.create_task(discovery.run()),
        asyncio.create_task(config_sync.run()),
        asyncio.create_task(capture.run()),
    ]

    logger.info("GrowCopilot add-on started")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
