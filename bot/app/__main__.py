"""Запуск: python -m app"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from aiohttp import web

from . import client, followups, team
from .config import load
from .db import DB
from .web import make_app


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load()
    db = DB(config.db_path)
    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(db=db, config=config)
    dp.include_router(team.router)   # чат команды — первым, чтобы reply не ушли в клиентский роутер
    dp.include_router(client.router)

    await bot.set_my_commands(
        [BotCommand(command="start", description="Начать"), BotCommand(command="menu", description="Меню"),
         BotCommand(command="cancel", description="Отменить заявку")],
        scope=BotCommandScopeAllPrivateChats(),
    )
    if config.team_chat_id:
        try:
            await bot.set_my_commands(
                [BotCommand(command="stats", description="Воронки за 30 дней (/stats 7 — за неделю)")],
                scope=BotCommandScopeChat(chat_id=config.team_chat_id),
            )
        except Exception:
            logging.warning("Бот не видит чат команды %s — добавьте его в чат", config.team_chat_id)
    else:
        logging.warning("TEAM_CHAT_ID не задан: добавьте бота в чат команды и напишите там /chatid")
    await bot.set_my_short_description("Инженеры для сайтов и сервисов без своего DevOps. Аудит, сопровождение, аварийная помощь.")
    await bot.set_my_description(
        "RootLab — команда инженеров из Екатеринбурга. Берём на себя серверы, резервные копии, мониторинг "
        "и выпуск обновлений. Нажмите «Старт» — подберём, с чего начать."
    )

    runner = web.AppRunner(make_app(bot, db, config))
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", config.web_port).start()
    reminders = asyncio.create_task(followups.loop(bot, db, config))
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        reminders.cancel()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
