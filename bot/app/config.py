"""Настройки из переменных окружения (файл .env рядом с docker-compose.yml)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int(name: str, default: int) -> int:
    v = os.getenv(name, "").strip()
    return int(v) if v else default


@dataclass
class Config:
    bot_token: str
    team_chat_id: int | None
    db_path: str = "/data/bot.sqlite3"
    web_port: int = 8080
    allowed_origins: list[str] = field(default_factory=list)
    remind_first_min: int = 60
    remind_second_min: int = 24 * 60
    work_hours: str = "с 9 до 21 по Екатеринбургу"


def load() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Не задан BOT_TOKEN (см. .env.example)")
    chat = os.getenv("TEAM_CHAT_ID", "").strip()
    origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "https://root-lab.ru").split(",") if o.strip()]
    return Config(
        bot_token=token,
        team_chat_id=int(chat) if chat else None,
        db_path=os.getenv("DB_PATH", "/data/bot.sqlite3"),
        web_port=_int("WEB_PORT", 8080),
        allowed_origins=origins,
        remind_first_min=_int("REMIND_FIRST_MIN", 60),
        remind_second_min=_int("REMIND_SECOND_MIN", 24 * 60),
    )
