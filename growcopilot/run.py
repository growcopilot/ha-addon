"""GrowCopilot Home Assistant Add-on entry point."""
import asyncio
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("growcopilot")

# Debug: find SUPERVISOR_TOKEN from all possible sources
import pathlib
_token_found = False

# 1. Check env var
_sv_token = os.environ.get("SUPERVISOR_TOKEN", "")
if _sv_token:
    logger.info("SUPERVISOR_TOKEN from env: %d chars", len(_sv_token))
    _token_found = True

# 2. Check s6 container environment files
for _s6_dir in ["/run/s6/container_environment", "/var/run/s6/container_environment"]:
    _s6_path = pathlib.Path(_s6_dir)
    if _s6_path.is_dir():
        logger.info("Found s6 env dir: %s — files: %s", _s6_dir, list(_s6_path.iterdir()))
        _token_file = _s6_path / "SUPERVISOR_TOKEN"
        if _token_file.exists():
            _val = _token_file.read_text().strip()
            logger.info("SUPERVISOR_TOKEN from s6 file: %d chars", len(_val))
            os.environ["SUPERVISOR_TOKEN"] = _val
            _token_found = True

# 3. Dump ALL env vars if token still not found
if not _token_found:
    logger.warning("SUPERVISOR_TOKEN not found anywhere. All env vars:")
    for key in sorted(os.environ):
        logger.warning("  %s = %s", key, os.environ[key][:50])


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
