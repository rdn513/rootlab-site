import asyncio
import time

from aiohttp.test_utils import TestClient, TestServer

from app.config import Config
from app.db import DB
from app.web import make_app
from tests.test_dialogs import FakeSession
from aiogram import Bot


def test_form_lead_goes_to_team_with_cors(tmp_path):
    async def go():
        session = FakeSession()
        bot = Bot("42:TEST", session=session)
        cfg = Config(bot_token="x", team_chat_id=-1, db_path=str(tmp_path / "w.db"),
                     allowed_origins=["https://root-lab.ru"])
        app = make_app(bot, DB(cfg.db_path), cfg)
        async with TestClient(TestServer(app)) as c:
            pre = await c.options("/lead", headers={"Origin": "https://root-lab.ru"})
            assert pre.headers["Access-Control-Allow-Origin"] == "https://root-lab.ru"
            r = await c.post("/lead", json={"name": "Анна", "contact": "+7 900", "consent": "on", "page": "/"},
                             headers={"Origin": "https://root-lab.ru"})
            assert r.status == 200 and (await r.json())["ok"]
            bad = await c.post("/lead", json={"name": "Анна", "contact": "+7 900"})
            assert bad.status == 422
            evil = await c.post("/lead", json={"name": "x", "contact": "y", "consent": "on"},
                                headers={"Origin": "https://evil.example"})
            assert "Access-Control-Allow-Origin" not in evil.headers
        return session
    session = asyncio.run(go())
    cards = [d["text"] for n, d in session.calls if n == "SendMessage"]
    assert any("Заявка с формы сайта" in t and "Анна" in t for t in cards)
