"""Диалоги целиком: бот + имитация Telegram API (без сети)."""
import asyncio
import json
import time
from itertools import count

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.base import BaseSession
from aiogram.enums import ParseMode
from aiogram.types import Update

from app import client, followups, team
from app.config import Config
from app.db import DB

TEAM = -100500
USER = 777


class FakeSession(BaseSession):
    """Записывает все запросы бота и отвечает правдоподобными объектами."""

    def __init__(self):
        super().__init__()
        self.calls = []
        self.ids = count(1000)

    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        data = method.model_dump()
        self.calls.append((name, data))
        if name in ("SendMessage", "EditMessageText"):
            chat = data.get("chat_id") or USER
            return method.__returning__.model_validate({
                "message_id": next(self.ids), "date": int(time.time()),
                "chat": {"id": chat, "type": "private" if chat > 0 else "supergroup"},
                "text": data.get("text", ""),
            }, context={"bot": bot}) if name == "SendMessage" else True
        if name == "CopyMessage":
            return method.__returning__.model_validate({"message_id": next(self.ids)})
        return True

    async def close(self):
        pass

    async def stream_content(self, *a, **k):  # pragma: no cover
        yield b""

    def texts(self, chat_id=None):
        return [d["text"] for n, d in self.calls if n == "SendMessage" and (chat_id is None or d["chat_id"] == chat_id)]


@pytest.fixture
def env(tmp_path):
    session = FakeSession()
    bot = Bot("42:TEST", session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    config = Config(bot_token="x", team_chat_id=TEAM, db_path=str(tmp_path / "t.db"))
    db = DB(config.db_path)
    dp = Dispatcher(db=db, config=config)
    for r in (team.router, client.router):
        r._parent_router = None  # роутеры модульные — отцепляем от прошлого теста
        dp.include_router(r)
    uid = count(1)

    def chat(cid):
        return {"id": cid, "type": "private" if cid > 0 else "supergroup", **({"first_name": "Иван"} if cid > 0 else {"title": "Команда"})}

    async def msg(text=None, chat_id=USER, reply_to=None, contact=None, from_id=USER):
        m = {"message_id": next(uid), "date": int(time.time()), "chat": chat(chat_id),
             "from": {"id": from_id, "is_bot": False, "first_name": "Иван", "username": "ivan"}}
        if text is not None:
            m["text"] = text
            if text.startswith("/"):
                m["entities"] = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]
        if contact:
            m["contact"] = contact
        if reply_to:
            m["reply_to_message"] = {"message_id": reply_to, "date": int(time.time()), "chat": chat(chat_id)}
        await dp.feed_update(bot, Update.model_validate({"update_id": next(uid), "message": m}, context={"bot": bot}))

    async def press(data, chat_id=USER, from_id=USER):
        cq = {"id": str(next(uid)), "chat_instance": "1", "data": data,
              "from": {"id": from_id, "is_bot": False, "first_name": "Дмитрий"},
              "message": {"message_id": 1, "date": int(time.time()), "chat": chat(chat_id), "text": "вопрос"}}
        await dp.feed_update(bot, Update.model_validate({"update_id": next(uid), "callback_query": cq}, context={"bot": bot}))

    return session, db, msg, press


def run(coro):
    return asyncio.run(coro)


def test_audit_funnel_end_to_end(env):
    session, db, msg, press = env

    async def go():
        await msg("/start site_hero")
        await press("a:who:0")            # веб-студия
        await msg("example.ru")           # сайт
        await press("a:servers:1")        # 2–3
        await press("a:hosting:0")        # VPS
        await press("skip:pain")
        await press("c:tg")
        await press("consent:yes")
    run(go())
    team_cards = session.texts(TEAM)
    assert len(team_cards) == 1
    card = team_cards[0]
    assert "Экспресс-аудит" in card and "Веб-студия" in card and "example.ru" in card
    assert "site_hero · главная, первый экран" in card and "в Telegram" in card
    assert any("Заявка у команды" in t for t in session.texts(USER))
    assert db.last_lead_of_user(USER)["funnel"] == "audit"


def test_emergency_with_phone_and_urgent_card(env):
    session, db, msg, press = env

    async def go():
        await msg("/start site_emergency")
        await msg("shop.ru")
        await press("a:symptom:1")
        await press("a:access:0")
        await press("c:phone")
        await msg(contact={"phone_number": "79120001122", "first_name": "Иван", "user_id": USER})
        await press("consent:yes")
    run(go())
    card = session.texts(TEAM)[0]
    assert "СРОЧНО" in card and "+79120001122" in card and "500" in card
    assert any("Пока ждёте" in t for t in session.texts(USER))


def test_prefill_from_tag_skips_question(env):
    session, db, msg, press = env
    run(msg("/start site_migration"))
    asked = session.texts(USER)
    assert not any("Что нужно?" in t for t in asked)
    assert db.active_session(USER)["awaiting"] == "site"


def test_relay_both_ways_and_status(env):
    session, db, msg, press = env

    async def go():
        await msg("/start site_hero_question")
        await msg("Можно ли перенести Битрикс?")
        await press("skip:site")
        await press("c:tg")
        await press("consent:yes")
        lead = db.last_lead_of_user(USER)
        # команда отвечает reply на карточку
        await msg("Да, можно", chat_id=TEAM, reply_to=lead["team_message_id"], from_id=1)
        # клиент пишет ещё
        await msg("Спасибо, а сроки?")
        # статус
        await press(f"lead:{lead['id']}:contacted", chat_id=TEAM, from_id=1)
        return lead
    lead = run(go())
    copies = [d for n, d in session.calls if n == "CopyMessage"]
    assert any(d["chat_id"] == USER for d in copies), "ответ команды не дошёл клиенту"
    assert any(d["chat_id"] == TEAM for d in copies), "сообщение клиента не дошло команде"
    assert db.lead(lead["id"])["status"] == "contacted"


def test_private_reply_is_not_eaten_by_team_router(env):
    session, db, msg, press = env

    async def go():
        await msg("/start site_header")
        await msg("Вопрос как ответ", reply_to=5)
    run(go())
    s = db.active_session(USER)
    assert json.loads(s["answers"]).get("question") == "Вопрос как ответ"


def test_reminders_due(env):
    session, db, msg, press = env
    run(msg("/start site_pricing_basic"))
    s = db.active_session(USER)
    db.conn.execute("UPDATE sessions SET updated_at=? WHERE id=?", (time.time() - 3 * 3600, s["id"]))
    due = db.due_reminders(time.time(), 60, 1440, {})
    assert [r["id"] for r in due] == [s["id"]]
    assert "Сопровождение" in followups.reminder_text("support", 0)


def test_unknown_tag_shows_menu(env):
    session, db, msg, press = env
    run(msg("/start promo_x"))
    assert "С чем помочь?" in session.texts(USER)[-1]
