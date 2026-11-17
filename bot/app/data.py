"""Данные сайта (цены, тарифы, контакты, метки) — из site_data.json.

Файл генерируется командой `npm run build` из src/data/site.ts,
поэтому цены на сайте и в боте всегда совпадают.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

NBSP = " "
DATA_PATH = Path(__file__).with_name("site_data.json")


@lru_cache(maxsize=1)
def site() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def num(n: int) -> str:
    s = f"{n:,}".replace(",", NBSP)
    return s


def rub(n: int, unit: str = "₽") -> str:
    return f"{num(n)}{NBSP}{unit}"


def product(pid: str) -> dict:
    for p in site()["products"]:
        if p["id"] == pid:
            return p
    raise KeyError(pid)


def product_price(pid: str) -> str:
    p = product(pid)
    prefix = f"от{NBSP}" if p.get("priceFrom") else ""
    return prefix + rub(p["price"], p.get("unit") or "₽")


def plan(pid: str) -> dict:
    for p in site()["plans"]:
        if p["id"] == pid:
            return p
    raise KeyError(pid)


def tag_value(key: str) -> str:
    """Ключ метки (как в site.ts) → значение ?start=…"""
    return site()["botTags"][key]


def tag_key(value: str) -> str | None:
    """Значение ?start=… → ключ метки."""
    for k, v in site()["botTags"].items():
        if v == value:
            return k
    return None
