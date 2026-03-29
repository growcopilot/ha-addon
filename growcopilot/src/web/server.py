"""Ingress web server for the add-on."""
import asyncio
import logging
import aiohttp_jinja2
import jinja2
from pathlib import Path
from aiohttp import web
from src.web.routes import setup_routes

logger = logging.getLogger("growcopilot.web")
TEMPLATES_DIR = Path(__file__).parent / "templates"

async def start_server(port: int, gc_client, discovery_loop) -> None:
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)))
    app["gc_client"] = gc_client
    app["discovery"] = discovery_loop
    setup_routes(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Ingress UI running on port %d", port)
    while True:
        await asyncio.sleep(3600)
