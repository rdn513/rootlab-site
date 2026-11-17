"""HTTP-приём заявок с формы сайта: POST /lead (JSON) → карточка в чат команды."""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque

from aiogram import Bot
from aiohttp import web

from .client import post_to_team
from .config import Config
from .db import DB

log = logging.getLogger(__name__)
LIMITS = {"name": 100, "contact": 100, "site": 200, "message": 2000, "source": 50, "page": 200}
RATE = (5, 600)  # не больше 5 заявок с одного IP за 10 минут


def validate(data: dict) -> tuple[dict | None, str | None]:
    if not isinstance(data, dict):
        return None, "bad_json"
    if data.get("company_website"):
        return None, "spam"
    clean = {k: str(data.get(k) or "").strip()[:n] for k, n in LIMITS.items()}
    if not clean["name"] or not clean["contact"]:
        return None, "required"
    if data.get("consent") not in ("on", True, "true", "yes"):
        return None, "consent"
    return clean, None


def make_app(bot: Bot, db: DB, config: Config) -> web.Application:
    hits: dict[str, deque] = defaultdict(deque)

    def cors(request: web.Request, resp: web.StreamResponse) -> web.StreamResponse:
        origin = request.headers.get("Origin", "")
        if origin in config.allowed_origins:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    async def options(request: web.Request):
        return cors(request, web.Response(status=204))

    async def lead(request: web.Request):
        ip = request.headers.get("X-Forwarded-For", request.remote or "").split(",")[0].strip()
        q = hits[ip]
        now = time.time()
        while q and now - q[0] > RATE[1]:
            q.popleft()
        if len(q) >= RATE[0]:
            return cors(request, web.json_response({"ok": False, "error": "rate"}, status=429))
        q.append(now)
        try:
            data = await request.json()
        except Exception:
            return cors(request, web.json_response({"ok": False, "error": "bad_json"}, status=400))
        clean, err = validate(data)
        if err == "spam":
            return cors(request, web.json_response({"ok": True}))
        if err:
            return cors(request, web.json_response({"ok": False, "error": err}, status=422))
        source = f"form:{clean['page'] or clean['source']}"
        lead_id = db.add_lead("form", source, {"kind": "form", "data": clean})
        db.event("submit", None, "form", source)
        try:
            await post_to_team(bot, db, config, lead_id)
        except Exception:
            log.exception("Не удалось отправить заявку #%s в чат", lead_id)
        return cors(request, web.json_response({"ok": True}))

    async def health(_request: web.Request):
        return web.json_response({"ok": True})

    app = web.Application(client_max_size=64 * 1024)
    app.router.add_route("OPTIONS", "/lead", options)
    app.router.add_post("/lead", lead)
    app.router.add_get("/health", health)
    return app
