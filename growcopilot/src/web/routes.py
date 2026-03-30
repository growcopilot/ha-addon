"""Web UI routes for the ingress panel."""
import json
import logging
import time
from pathlib import Path
import aiohttp_jinja2
from aiohttp import web
from src.gc_client import GrowCopilotClient
from src.discovery import DiscoveryLoop
from src.capture import CaptureLoop

logger = logging.getLogger("growcopilot.web.routes")
STATIC_DIR = Path(__file__).parent.parent.parent / "static"


def _base(request: web.Request) -> str:
    """Extract the HA ingress base path from the request header."""
    return request.headers.get("X-Ingress-Path", "").rstrip("/")


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
    return {"has_token": bool(gc.api_token), "page": "setup", "base": _base(request)}


@aiohttp_jinja2.template("setup.html")
async def handle_setup(request: web.Request) -> dict:
    gc: GrowCopilotClient = request.app["gc_client"]
    error = request.query.get("error")
    return {"has_token": bool(gc.api_token), "page": "setup", "error": error, "base": _base(request)}


async def handle_setup_post(request: web.Request) -> web.Response:
    base = _base(request)
    gc: GrowCopilotClient = request.app["gc_client"]
    data = await request.post()
    token = str(data.get("api_token", "")).strip()
    if not token.startswith("gc_"):
        raise web.HTTPFound(f"{base}/setup?error=invalid_format")
    gc.set_token(token)
    valid = await gc.validate_token()
    if not valid:
        gc.set_token("")
        raise web.HTTPFound(f"{base}/setup?error=invalid_token")
    options_path = Path("/data/options.json")
    options = {}
    try:
        options = json.loads(options_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    options["api_token"] = token
    options_path.parent.mkdir(parents=True, exist_ok=True)
    options_path.write_text(json.dumps(options))
    # Also persist token separately (survives HA addon updates that reset options.json)
    Path("/data/gc_token").write_text(token)
    raise web.HTTPFound(f"{base}/entities")


@aiohttp_jinja2.template("entities.html")
async def handle_entities(request: web.Request) -> dict:
    discovery: DiscoveryLoop = request.app["discovery"]
    if not discovery.discovered:
        await discovery.discover_once()
    saved = request.query.get("saved")
    return {"entities": discovery.discovered, "selected_ids": discovery.selected_ids, "page": "entities", "saved": saved, "base": _base(request)}


async def handle_entities_post(request: web.Request) -> web.Response:
    base = _base(request)
    discovery: DiscoveryLoop = request.app["discovery"]
    data = await request.post()
    selected = [e["entityId"] for e in discovery.discovered if data.get(e["entityId"])]
    discovery.select_entities(selected)
    await discovery.push_selected()
    raise web.HTTPFound(f"{base}/entities?saved=1")


@aiohttp_jinja2.template("status.html")
async def handle_status(request: web.Request) -> dict:
    gc: GrowCopilotClient = request.app["gc_client"]
    discovery: DiscoveryLoop = request.app["discovery"]
    capture: CaptureLoop | None = request.app.get("capture")

    now = time.time()
    camera_targets = []
    for entity_id, target in (capture.targets if capture else {}).items():
        last_ts = capture._last_capture.get(entity_id, 0) if capture else 0
        interval = target.get("intervalSec", 900)
        next_in = max(0, int(interval - (now - last_ts))) if last_ts else 0
        friendly = entity_id
        for e in discovery.discovered:
            if e["entityId"] == entity_id:
                friendly = e.get("friendlyName", entity_id)
                break
        camera_targets.append({
            "entityId": entity_id,
            "friendlyName": friendly,
            "growSpaceId": target.get("growSpaceId", ""),
            "intervalSec": interval,
            "lastCapture": int(now - last_ts) if last_ts else None,
            "nextIn": next_in if last_ts else interval,
        })

    selected_sensors = [
        e for e in discovery.discovered
        if e["entityId"] in discovery.selected_ids and e["entityType"] == "sensor"
    ]

    return {
        "has_token": bool(gc.api_token),
        "page": "status",
        "base": _base(request),
        "selected_count": len(discovery.selected_ids),
        "discovered_count": len(discovery.discovered),
        "camera_targets": camera_targets,
        "sensors": selected_sensors,
    }
