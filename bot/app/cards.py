"""Карточки заявок для чата команды: текст и кнопки статусов."""
from __future__ import annotations

from html import escape

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .funnels import FUNNELS, PREFILL_LABELS, TAG_PLACE
from .data import tag_key

STATUS = {
    "new": "🆕 Новая — нажмите «Беру»",
    "taken": "✋ В работе: {by}",
    "contacted": "✅ Связались: {by}",
    "rejected": "🚫 Не целевая: {by}",
}


def answer_lines(funnel_id: str, answers: dict) -> list[tuple[str, str]]:
    """Ответы клиента в виде пар (подпись, значение) в порядке вопросов."""
    f = FUNNELS[funnel_id]
    out: list[tuple[str, str]] = []
    for key, (label, values) in PREFILL_LABELS.items():
        if key in answers:
            out.append((label, values.get(answers[key], answers[key])))
    for s in f.steps:
        if s.key not in answers:
            continue
        v = answers[s.key]
        if s.key == "contact_way":
            v = "в Telegram" if v == "tg" else f"позвонить: {v.removeprefix('phone:')}"
        elif v == "":
            v = "—"
        elif s.options:
            v = dict(s.options).get(v, v)
        out.append((s.label or s.key, v))
    return out


def source_line(source: str | None) -> str:
    if not source:
        return "—"
    if source == "bot_menu":
        return "бот, меню без метки"
    if source.startswith("form:"):
        return f"форма на сайте ({source.removeprefix('form:')})"
    key = tag_key(source)
    place = TAG_PLACE.get(key or "", "")
    return f"{source}" + (f" · {place}" if place else "")


def client_line(user_id: int | None, first_name: str | None, username: str | None) -> str:
    name = escape(first_name or "Без имени")
    if user_id:
        name = f'<a href="tg://user?id={user_id}">{name}</a>'
    if username:
        name += f" @{escape(username)}"
    return name


def bot_card(lead_id: int, funnel_id: str, source: str | None, user_id: int, first_name: str | None,
             username: str | None, answers: dict, status: str = "new", by: str | None = None) -> str:
    f = FUNNELS[funnel_id]
    head = f"{f.emoji} <b>{'СРОЧНО · ' if f.urgent else ''}{escape(f.title)}</b> · заявка #{lead_id}"
    lines = [head, "", f"Клиент: {client_line(user_id, first_name, username)}"]
    for label, v in answer_lines(funnel_id, answers):
        lines.append(f"{escape(label)}: {escape(str(v))}")
    lines += ["", f"Источник: {escape(source_line(source))}", "", STATUS[status].format(by=escape(by or ""))]
    lines.append("<i>Ответьте на это сообщение (reply) — бот перешлёт ответ клиенту.</i>")
    return "\n".join(lines)


def form_card(lead_id: int, data: dict, status: str = "new", by: str | None = None) -> str:
    rows = [
        ("Имя", data.get("name")),
        ("Контакт", data.get("contact")),
        ("Сайт", data.get("site") or "—"),
        ("Что беспокоит", data.get("message") or "—"),
        ("Согласие на обработку ПДн", "да"),
    ]
    lines = [f"📝 <b>Заявка с формы сайта</b> · #{lead_id}", ""]
    lines += [f"{k}: {escape(str(v))}" for k, v in rows]
    lines += ["", f"Источник: {escape(source_line('form:' + (data.get('page') or data.get('source') or '')))}",
              "", STATUS[status].format(by=escape(by or ""))]
    lines.append("<i>Клиент оставил контакт — свяжитесь с ним напрямую.</i>")
    return "\n".join(lines)


def lead_keyboard(lead_id: int, status: str) -> InlineKeyboardMarkup | None:
    if status in ("contacted", "rejected"):
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="↩ Вернуть в работу", callback_data=f"lead:{lead_id}:taken"),
        ]])
    row = []
    if status == "new":
        row.append(InlineKeyboardButton(text="✋ Беру", callback_data=f"lead:{lead_id}:taken"))
    row.append(InlineKeyboardButton(text="✅ Связались", callback_data=f"lead:{lead_id}:contacted"))
    row.append(InlineKeyboardButton(text="🚫 Не целевая", callback_data=f"lead:{lead_id}:rejected"))
    return InlineKeyboardMarkup(inline_keyboard=[row])
