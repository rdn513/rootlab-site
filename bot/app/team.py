"""Чат команды: статусы заявок, ответы клиентам, статистика."""
from __future__ import annotations

import json
import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message, ReactionTypeEmoji

from . import cards
from .config import Config
from .db import DB
from .funnels import FUNNELS

log = logging.getLogger(__name__)
router = Router(name="team")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))
router.callback_query.filter(F.message.chat.type.in_({"group", "supergroup"}))


@router.message(Command("chatid"))
async def chat_id(message: Message):
    """Помогает настроить TEAM_CHAT_ID: напишите /chatid в чате команды."""
    await message.reply(f"ID этого чата: <code>{message.chat.id}</code>\nВпишите его в TEAM_CHAT_ID и перезапустите бота.")


def _is_team(message_or_cb, config: Config) -> bool:
    chat = message_or_cb.chat if isinstance(message_or_cb, Message) else message_or_cb.message.chat
    return config.team_chat_id is not None and chat.id == config.team_chat_id


def render(lead) -> tuple[str, object]:
    p = json.loads(lead["payload"])
    if p["kind"] == "bot":
        text = cards.bot_card(lead["id"], p["funnel"], p["source"], p["user_id"], p["first_name"],
                              p["username"], p["answers"], lead["status"], lead["taken_by"])
    else:
        text = cards.form_card(lead["id"], p["data"], lead["status"], lead["taken_by"])
    return text, cards.lead_keyboard(lead["id"], lead["status"])


@router.callback_query(F.data.startswith("lead:"))
async def on_status(cb: CallbackQuery, db: DB, config: Config):
    if not _is_team(cb, config):
        await cb.answer()
        return
    _, lead_id, status = cb.data.split(":")
    lead = db.lead(int(lead_id))
    if not lead:
        await cb.answer("Заявка не найдена")
        return
    by = cb.from_user.first_name or cb.from_user.username or "—"
    db.set_lead_status(lead["id"], status, by)
    text, markup = render(db.lead(lead["id"]))
    await cb.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    await cb.answer({"taken": "Заявка ваша", "contacted": "Отмечено", "rejected": "Отмечено"}.get(status, "Ок"))


@router.message(Command("stats"))
async def stats(message: Message, command: CommandObject, db: DB, config: Config):
    if not _is_team(message, config):
        return
    days = int(command.args) if command.args and command.args.isdigit() else 30
    st = db.stats(days)
    starts = {r["funnel"]: r["n"] for r in st["starts"]}
    leads = {r["funnel"]: r["n"] for r in st["leads"]}
    lines = [f"<b>Воронки за {days} дн.</b>", "<code>воронка        начали → заявки</code>"]
    for fid, f in FUNNELS.items():
        s, l = starts.get(fid, 0), leads.get(fid, 0)
        if s or l:
            conv = f"{round(100 * l / s)}%" if s else "—"
            lines.append(f"<code>{f.title[:14]:<14} {s:>5} → {l:<4} {conv}</code>")
    if leads.get("form"):
        lines.append(f"<code>{'Форма сайта':<14} {'—':>5} → {leads['form']:<4}</code>")
    if st["sources"]:
        lines += ["", "<b>Источники заявок</b>"] + [f"{escape(str(r['source']))}: {r['n']}" for r in st["sources"]]
    if st["statuses"]:
        lines += ["", "<b>Статусы</b>"] + [f"{r['status']}: {r['n']}" for r in st["statuses"]]
    if len(lines) == 2:
        lines.append("Пока пусто.")
    await message.answer("\n".join(lines))


@router.message(F.reply_to_message)
async def reply_to_client(message: Message, bot: Bot, db: DB, config: Config):
    """Ответ (reply) на карточку или сообщение клиента в чате команды → клиенту в личку."""
    if not _is_team(message, config) or (message.text or "").startswith("/"):
        return
    target = db.relay_target(message.reply_to_message.message_id)
    if not target:
        return
    try:
        await bot.send_message(target["user_id"], "Ответ команды RootLab:")
        await bot.copy_message(target["user_id"], message.chat.id, message.message_id)
    except Exception as e:  # клиент заблокировал бота и т. п.
        log.warning("Не доставлено клиенту %s: %s", target["user_id"], e)
        await message.reply("⚠️ Не доставлено: клиент заблокировал бота или удалил чат.")
        return
    db.link(message.message_id, target["user_id"], target["lead_id"])
    if target["lead_id"]:
        lead = db.lead(target["lead_id"])
        if lead and lead["status"] == "new":
            db.set_lead_status(lead["id"], "taken", message.from_user.first_name)
            if lead["team_message_id"]:
                text, markup = render(db.lead(lead["id"]))
                try:
                    await bot.edit_message_text(text, chat_id=message.chat.id, message_id=lead["team_message_id"],
                                                reply_markup=markup, disable_web_page_preview=True)
                except Exception:
                    pass
    try:
        await message.react([ReactionTypeEmoji(emoji="👌")])
    except Exception:
        await message.reply("✓ Отправлено клиенту")
