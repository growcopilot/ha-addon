"""Web UI routes for the ingress panel."""
import json
import logging
from pathlib import Path
import aiohttp_jinja2
from aiohttp import web
from src.gc_client import GrowCopilotClient
from src.discovery import DiscoveryLoop

logger = logging.getLogger("growcopilot.web.routes")
STATIC_DIR = Path(__file__).parent.parent.parent / "static"

def setup_routes(app: web.Application) -> None:
    app.router.add_get("/", handle_index)
    app.router.add_get("/setup", handle_setup)
    app.router.add_post("/setup", handle_setup_post)
    app.router.add_get("/entities", handle_entities)
    app.router.add_post("/entities", handle_entities_post)
    app.router.add_get("/status", handle_status)
    app.router.add_static("/static", STATIC_DIR)

@aiohttp_jinja2.template("setup.html")
async def handle_index(request: web.Request) -> dict:
    gc: GrowCopilotClient = request.app["gc_client"]
    return {"has_token": bool(gc.api_token), "page": "setup"}

@aiohttp_jinja2.template("setup.html")
async def handle_setup(request: web.Request) -> dict:
    gc: GrowCopilotClient = request.app["gc_client"]
    error = request.query.get("error")
    return {"has_token": bool(gc.api_token), "page": "setup", "error": error}

async def handle_setup_post(request: web.Request) -> web.Response:
    gc: GrowCopilotClient = request.app["gc_client"]
    data = await request.post()
    token = str(data.get("api_token", "")).strip()
    if not token.startswith("gc_"):
        raise web.HTTPFound("/setup?error=invalid_format")
    gc.set_token(token)
    valid = await gc.validate_token()
    if not valid:
        gc.set_token("")
        raise web.HTTPFound("/setup?error=invalid_token")
    options_path = Path("/data/options.json")
    options = {}
    try:
        options = json.loads(options_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    options["api_token"] = token
    options_path.parent.mkdir(parents=True, exist_ok=True)
    options_path.write_text(json.dumps(options))
    raise web.HTTPFound("/entities")

@aiohttp_jinja2.template("entities.html")
async def handle_entities(request: web.Request) -> dict:
    discovery: DiscoveryLoop = request.app["discovery"]
    if not discovery.discovered:
        await discovery.discover_once()
    saved = request.query.get("saved")
    return {"entities": discovery.discovered, "selected_ids": discovery.selected_ids, "page": "entities", "saved": saved}

async def handle_entities_post(request: web.Request) -> web.Response:
    discovery: DiscoveryLoop = request.app["discovery"]
    data = await request.post()
    selected = [e["entityId"] for e in discovery.discovered if data.get(e["entityId"])]
    discovery.select_entities(selected)
    await discovery.push_selected()
    raise web.HTTPFound("/entities?saved=1")

@aiohttp_jinja2.template("status.html")
async def handle_status(request: web.Request) -> dict:
    gc: GrowCopilotClient = request.app["gc_client"]
    return {"has_token": bool(gc.api_token), "page": "status"}
