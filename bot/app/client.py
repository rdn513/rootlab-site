"""Диалог с клиентом в личке бота: воронки, согласие, отправка заявки."""
from __future__ import annotations

import json
import logging
import re
from html import escape

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from . import cards
from .config import Config
from .data import site
from .db import DB
from .funnels import FUNNELS, MENU, Funnel, Step, next_step, resolve

log = logging.getLogger(__name__)
router = Router(name="client")
router.message.filter(F.chat.type == "private")
router.callback_query.filter(F.message.chat.type == "private")

PHONE_RE = re.compile(r"^\+?[\d\s()\-]{10,20}$")
MAX_TEXT = 1500


# ---------- клавиатуры ----------

def kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows]
    )


def menu_kb() -> InlineKeyboardMarkup:
    return kb([[(label, f"menu:{fid}")] for fid, label in MENU])


def step_kb(step: Step) -> InlineKeyboardMarkup | None:
    rows: list[list[tuple[str, str]]] = []
    if step.kind == "choice":
        rows = [[(label, f"a:{step.key}:{i}")] for i, (_, label) in enumerate(step.options)]
    elif step.kind == "contact":
        rows = [[(label, f"c:{value}")] for value, label in step.options]
    if step.skippable:
        rows.append([("Пропустить", f"skip:{step.key}")])
    return kb(rows) if rows else None


# ---------- шаги ----------

def progress(f: Funnel, answers: dict, step: Step) -> str:
    todo = [s for s in f.steps if s.key not in answers and not (s.when and not s.when(answers))]
    done = sum(1 for s in f.steps if s.key in answers)
    total = done + len(todo)
    return f"{done + 1}/{total}"


async def ask(bot: Bot, db: DB, chat_id: int, sid: int) -> None:
    s = db.session(sid)
    f = FUNNELS[s["funnel"]]
    answers = json.loads(s["answers"])
    step = next_step(f, answers)
    if step is None:
        await ask_consent(bot, db, chat_id, sid)
        return
    db.save_answers(sid, answers, step.key)
    hint = "\n<i>Напишите ответ сообщением.</i>" if step.kind == "text" else ""
    await bot.send_message(chat_id, f"<code>{progress(f, answers, step)}</code> {step.text}{hint}",
                           reply_markup=step_kb(step))


async def ask_consent(bot: Bot, db: DB, chat_id: int, sid: int) -> None:
    s = db.session(sid)
    answers = json.loads(s["answers"])
    db.save_answers(sid, answers, "consent")
    summary = "\n".join(f"• {escape(k)}: {escape(str(v))}" for k, v in cards.answer_lines(s["funnel"], answers))
    text = (
        f"<b>Проверьте заявку</b>\n{summary}\n\n"
        "Нажимая «Отправить», вы соглашаетесь на обработку персональных данных "
        f"(имя в Telegram, контакт и ответы выше) по <a href=\"{site()['privacyUrl']}\">политике</a>."
    )
    await bot.send_message(chat_id, text, disable_web_page_preview=True, reply_markup=kb([
        [("✅ Отправить заявку", "consent:yes")],
        [("✏️ Заполнить заново", "consent:restart"), ("✖ Отменить", "consent:no")],
    ]))


async def submit(bot: Bot, db: DB, config: Config, chat_id: int, sid: int) -> None:
    s = db.session(sid)
    f = FUNNELS[s["funnel"]]
    answers = json.loads(s["answers"])
    payload = {
        "kind": "bot", "funnel": f.id, "source": s["source"], "user_id": s["user_id"],
        "first_name": s["first_name"], "username": s["username"], "answers": answers,
    }
    lead_id = db.add_lead(f.id, s["source"], payload, session_id=sid, user_id=s["user_id"])
    db.set_status(sid, "submitted")
    db.event("submit", s["user_id"], f.id, s["source"])
    await post_to_team(bot, db, config, lead_id)
    await bot.send_message(chat_id, f.done(answers), reply_markup=ReplyKeyboardRemove())
    await bot.send_message(chat_id, "Если хотите что-то добавить — просто напишите сюда, сообщение уйдёт команде.")


async def post_to_team(bot: Bot, db: DB, config: Config, lead_id: int) -> None:
    lead = db.lead(lead_id)
    p = json.loads(lead["payload"])
    if not config.team_chat_id:
        log.error("TEAM_CHAT_ID не задан — заявка #%s сохранена только в базе", lead_id)
        return
    if p["kind"] == "bot":
        text = cards.bot_card(lead_id, p["funnel"], p["source"], p["user_id"], p["first_name"],
                              p["username"], p["answers"])
    else:
        text = cards.form_card(lead_id, p["data"])
    msg = await bot.send_message(config.team_chat_id, text, reply_markup=cards.lead_keyboard(lead_id, "new"),
                                 disable_web_page_preview=True)
    db.set_lead_message(lead_id, msg.message_id)
    if p["kind"] == "bot":
        db.link(msg.message_id, p["user_id"], lead_id)


async def start_funnel(bot: Bot, db: DB, message_or_user, funnel: Funnel, source: str | None, prefill: dict) -> None:
    u = message_or_user
    sid = db.start_session(u.id, u.username, u.first_name, funnel.id, source, prefill)
    db.event("start", u.id, funnel.id, source)
    await bot.send_message(u.id, funnel.intro(), disable_web_page_preview=True)
    await ask(bot, db, u.id, sid)


# ---------- команды ----------

@router.message(CommandStart())
async def on_start(message: Message, command: CommandObject, bot: Bot, db: DB):
    funnel, _key, prefill = resolve(command.args)
    if funnel:
        await start_funnel(bot, db, message.from_user, funnel, command.args, prefill)
        return
    db.event("open", message.from_user.id, None, command.args or None)
    await message.answer(
        "Здравствуйте! Это команда RootLab — инженеры для сайтов и сервисов, которым рано нанимать своего DevOps.\n\n"
        "С чем помочь?",
        reply_markup=menu_kb(),
    )


@router.message(Command("menu"))
async def on_menu(message: Message):
    await message.answer("С чем помочь?", reply_markup=menu_kb())


@router.message(Command("cancel"))
async def on_cancel(message: Message, db: DB):
    s = db.active_session(message.from_user.id)
    if s:
        db.set_status(s["id"], "cancelled")
    await message.answer("Отменили. Вернуться — /start.", reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data.startswith("menu:"))
async def on_menu_pick(cb: CallbackQuery, bot: Bot, db: DB):
    fid = cb.data.split(":", 1)[1]
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    if fid in FUNNELS:
        await start_funnel(bot, db, cb.from_user, FUNNELS[fid], "bot_menu", {})


# ---------- ответы на вопросы ----------

async def _current(cb: CallbackQuery, db: DB, expected_key: str | None):
    s = db.active_session(cb.from_user.id)
    if not s or (expected_key and s["awaiting"] != expected_key):
        await cb.answer("Этот вопрос уже позади", show_alert=False)
        return None
    return s


async def _mark_answer(cb: CallbackQuery, label: str):
    try:
        await cb.message.edit_text(f"{cb.message.html_text}\n→ <b>{escape(label)}</b>", reply_markup=None)
    except Exception:  # сообщение могло устареть — не критично
        await cb.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("a:"))
async def on_choice(cb: CallbackQuery, bot: Bot, db: DB):
    _, key, idx = cb.data.split(":", 2)
    s = await _current(cb, db, key)
    if not s:
        return
    f = FUNNELS[s["funnel"]]
    step = next(x for x in f.steps if x.key == key)
    value, label = step.options[int(idx)]
    answers = json.loads(s["answers"])
    answers[key] = value
    db.save_answers(s["id"], answers, None)
    await cb.answer()
    await _mark_answer(cb, label)
    if step.note and (note := step.note(answers)):
        await bot.send_message(cb.from_user.id, note)
    await ask(bot, db, cb.from_user.id, s["id"])


@router.callback_query(F.data.startswith("skip:"))
async def on_skip(cb: CallbackQuery, bot: Bot, db: DB):
    key = cb.data.split(":", 1)[1]
    s = await _current(cb, db, key)
    if not s:
        return
    answers = json.loads(s["answers"])
    answers[key] = ""
    db.save_answers(s["id"], answers, None)
    await cb.answer()
    await _mark_answer(cb, "пропущено")
    await ask(bot, db, cb.from_user.id, s["id"])


@router.callback_query(F.data.startswith("c:"))
async def on_contact_way(cb: CallbackQuery, bot: Bot, db: DB):
    way = cb.data.split(":", 1)[1]
    s = await _current(cb, db, "contact_way")
    if not s:
        return
    await cb.answer()
    answers = json.loads(s["answers"])
    if way == "tg":
        await _mark_answer(cb, "в Telegram")
        if not cb.from_user.username:
            await bot.send_message(cb.from_user.id,
                                   "У вашего аккаунта нет @username — ответим через этого бота.")
        answers["contact_way"] = "tg"
        db.save_answers(s["id"], answers, None)
        await ask(bot, db, cb.from_user.id, s["id"])
        return
    await _mark_answer(cb, "позвонить")
    db.save_answers(s["id"], answers, "phone")
    await bot.send_message(
        cb.from_user.id,
        "Нажмите кнопку ниже, чтобы поделиться номером, или напишите его сообщением.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True,
        ),
    )


@router.message(F.contact)
async def on_contact(message: Message, bot: Bot, db: DB):
    s = db.active_session(message.from_user.id)
    if not s or s["awaiting"] != "phone":
        return
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        await message.answer("Пришлите, пожалуйста, свой номер.")
        return
    phone = message.contact.phone_number
    phone = phone if phone.startswith("+") else "+" + phone
    answers = json.loads(s["answers"])
    answers["contact_way"] = f"phone:{phone}"
    db.save_answers(s["id"], answers, None)
    await message.answer(f"Номер {escape(phone)} — записали.", reply_markup=ReplyKeyboardRemove())
    await ask(bot, db, message.from_user.id, s["id"])


@router.callback_query(F.data.startswith("consent:"))
async def on_consent(cb: CallbackQuery, bot: Bot, db: DB, config: Config):
    action = cb.data.split(":", 1)[1]
    s = await _current(cb, db, "consent")
    if not s:
        return
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    if action == "yes":
        await submit(bot, db, config, cb.from_user.id, s["id"])
    elif action == "restart":
        _, _, prefill = resolve(s["source"])
        await start_funnel(bot, db, cb.from_user, FUNNELS[s["funnel"]], s["source"], prefill)
    else:
        db.set_status(s["id"], "cancelled")
        await bot.send_message(cb.from_user.id, "Заявку отменили. Если передумаете — /start.")


# ---------- напоминания: ответы на кнопки ----------

@router.callback_query(F.data.startswith("r:"))
async def on_reminder(cb: CallbackQuery, bot: Bot, db: DB):
    action = cb.data.split(":", 1)[1]
    s = db.active_session(cb.from_user.id)
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    if not s:
        await bot.send_message(cb.from_user.id, "С чем помочь?", reply_markup=menu_kb())
        return
    if action == "go":
        if s["awaiting"] == "consent":
            await ask_consent(bot, db, cb.from_user.id, s["id"])
        else:
            await ask(bot, db, cb.from_user.id, s["id"])
    else:
        db.stop_reminders(s["id"])
        await bot.send_message(cb.from_user.id, "Хорошо, не будем беспокоить. Вернуться можно командой /start.")


# ---------- свободный текст ----------

@router.message()
async def on_text(message: Message, bot: Bot, db: DB, config: Config):
    uid = message.from_user.id
    s = db.active_session(uid)
    text = (message.text or "").strip()

    if s and s["awaiting"] == "phone" and text:
        if not PHONE_RE.match(text):
            await message.answer("Не похоже на номер. Пример: +7 912 345-67-89")
            return
        answers = json.loads(s["answers"])
        answers["contact_way"] = f"phone:{text}"
        db.save_answers(s["id"], answers, None)
        await message.answer("Записали.", reply_markup=ReplyKeyboardRemove())
        await ask(bot, db, uid, s["id"])
        return

    if s and s["awaiting"]:
        f = FUNNELS[s["funnel"]]
        step = next((x for x in f.steps if x.key == s["awaiting"]), None)
        if step and step.kind == "text" and text:
            answers = json.loads(s["answers"])
            answers[step.key] = text[:MAX_TEXT]
            db.save_answers(s["id"], answers, None)
            await ask(bot, db, uid, s["id"])
            return
        if step and step.kind in ("choice", "contact"):
            await message.answer("Выберите вариант кнопкой выше — или /cancel, чтобы отменить.")
            return
        if s["awaiting"] == "consent":
            await message.answer("Нажмите «Отправить заявку» выше — или /cancel.")
            return

    # заявки нет в процессе — пересылаем сообщение команде, если клиент уже оставлял заявку
    lead = db.last_lead_of_user(uid)
    if lead and config.team_chat_id:
        who = cards.client_line(uid, message.from_user.first_name, message.from_user.username)
        head = await bot.send_message(
            config.team_chat_id, f"💬 Сообщение от {who} по заявке #{lead['id']}:",
            reply_to_message_id=lead["team_message_id"], disable_web_page_preview=True,
        ) if lead["team_message_id"] else None
        copy = await bot.copy_message(config.team_chat_id, message.chat.id, message.message_id,
                                      reply_to_message_id=head.message_id if head else None)
        db.link(copy.message_id, uid, lead["id"])
        if head:
            db.link(head.message_id, uid, lead["id"])
        await message.answer("Передали команде. Ответим здесь.")
        return

    await message.answer("С чем помочь?", reply_markup=menu_kb())
