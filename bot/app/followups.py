"""Напоминания тем, кто начал заявку и не закончил."""
from __future__ import annotations

import asyncio
import logging
import time

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .config import Config
from .db import DB
from .funnels import FUNNELS

log = logging.getLogger(__name__)


def reminder_text(funnel_id: str, n: int) -> str:
    f = FUNNELS[funnel_id]
    if f.urgent:
        return ("Сайт всё ещё не работает? Ответьте на вопросы выше — или просто опишите, что случилось, "
                "одним сообщением. Передадим инженеру.")
    if n == 0:
        return f"Вы начали заявку «{f.title}» и остановились. Осталось пару вопросов — продолжим?"
    return f"Напоминаем про заявку «{f.title}». Если неактуально — нажмите «Не сейчас», больше не напишем."


async def loop(bot: Bot, db: DB, config: Config, every_sec: int = 60) -> None:
    urgent = {fid: f.remind_after_min for fid, f in FUNNELS.items() if f.remind_after_min}
    while True:
        try:
            for s in db.due_reminders(time.time(), config.remind_first_min, config.remind_second_min, urgent):
                db.mark_reminded(s["id"])
                try:
                    await bot.send_message(
                        s["user_id"], reminder_text(s["funnel"], s["reminders"]),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(text="Продолжить", callback_data="r:go"),
                            InlineKeyboardButton(text="Не сейчас", callback_data="r:stop"),
                        ]]),
                    )
                except Exception as e:
                    log.info("Напоминание не доставлено %s: %s", s["user_id"], e)
                    db.stop_reminders(s["id"])
        except Exception:
            log.exception("Ошибка в цикле напоминаний")
        await asyncio.sleep(every_sec)
