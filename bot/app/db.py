"""Хранилище: SQLite-файл (путь — DB_PATH). Сессии воронок, заявки, связи для ответов."""
from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  username TEXT, first_name TEXT,
  funnel TEXT NOT NULL,
  source TEXT,                 -- значение ?start= или 'bot_menu'
  answers TEXT NOT NULL DEFAULT '{}',
  awaiting TEXT,               -- ключ вопроса, на который ждём ответ
  status TEXT NOT NULL DEFAULT 'active',   -- active | submitted | cancelled
  reminders INTEGER NOT NULL DEFAULT 0,
  no_remind INTEGER NOT NULL DEFAULT 0,
  started_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id, status);
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY,
  session_id INTEGER, user_id INTEGER,
  funnel TEXT NOT NULL, source TEXT,
  payload TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new',      -- new | taken | contacted | rejected
  taken_by TEXT,
  team_message_id INTEGER,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS relay (
  team_message_id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  lead_id INTEGER
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  user_id INTEGER, kind TEXT NOT NULL, funnel TEXT, source TEXT, at REAL NOT NULL
);
"""


class DB:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

    @contextmanager
    def tx(self):
        self.conn.execute("BEGIN")
        try:
            yield self.conn
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    # ---- события (для /stats) ----
    def event(self, kind: str, user_id: int | None, funnel: str | None, source: str | None):
        self.conn.execute(
            "INSERT INTO events(user_id, kind, funnel, source, at) VALUES (?,?,?,?,?)",
            (user_id, kind, funnel, source, time.time()),
        )

    # ---- сессии ----
    def start_session(self, user_id: int, username: str | None, first_name: str | None,
                      funnel: str, source: str | None, answers: dict) -> int:
        now = time.time()
        with self.tx() as c:
            c.execute("UPDATE sessions SET status='cancelled', updated_at=? WHERE user_id=? AND status='active'",
                      (now, user_id))
            cur = c.execute(
                "INSERT INTO sessions(user_id, username, first_name, funnel, source, answers, started_at, updated_at)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (user_id, username, first_name, funnel, source, json.dumps(answers, ensure_ascii=False), now, now),
            )
            return cur.lastrowid

    def active_session(self, user_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM sessions WHERE user_id=? AND status='active' ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone()

    def session(self, sid: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()

    def save_answers(self, sid: int, answers: dict, awaiting: str | None):
        self.conn.execute(
            "UPDATE sessions SET answers=?, awaiting=?, updated_at=?, reminders=0 WHERE id=?",
            (json.dumps(answers, ensure_ascii=False), awaiting, time.time(), sid),
        )

    def set_status(self, sid: int, status: str):
        self.conn.execute("UPDATE sessions SET status=?, updated_at=? WHERE id=?", (status, time.time(), sid))

    def stop_reminders(self, sid: int):
        self.conn.execute("UPDATE sessions SET no_remind=1 WHERE id=?", (sid,))

    def due_reminders(self, now: float, first_min: int, second_min: int, urgent_first: dict[str, int]):
        rows = self.conn.execute(
            "SELECT * FROM sessions WHERE status='active' AND no_remind=0 AND reminders<2"
        ).fetchall()
        out = []
        for r in rows:
            idle_min = (now - r["updated_at"]) / 60
            first = urgent_first.get(r["funnel"], first_min)
            if (r["reminders"] == 0 and idle_min >= first) or (r["reminders"] == 1 and idle_min >= second_min):
                out.append(r)
        return out

    def mark_reminded(self, sid: int):
        # updated_at не трогаем, чтобы второй интервал считался от последнего ответа клиента
        self.conn.execute("UPDATE sessions SET reminders=reminders+1 WHERE id=?", (sid,))

    # ---- заявки ----
    def add_lead(self, funnel: str, source: str | None, payload: dict,
                 session_id: int | None = None, user_id: int | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO leads(session_id, user_id, funnel, source, payload, created_at) VALUES (?,?,?,?,?,?)",
            (session_id, user_id, funnel, source, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        return cur.lastrowid

    def lead(self, lead_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()

    def set_lead_message(self, lead_id: int, message_id: int):
        self.conn.execute("UPDATE leads SET team_message_id=? WHERE id=?", (message_id, lead_id))

    def set_lead_status(self, lead_id: int, status: str, by: str | None):
        self.conn.execute("UPDATE leads SET status=?, taken_by=COALESCE(?, taken_by) WHERE id=?",
                          (status, by, lead_id))

    def last_lead_of_user(self, user_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM leads WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,)
        ).fetchone()

    # ---- переписка через чат команды ----
    def link(self, team_message_id: int, user_id: int, lead_id: int | None):
        self.conn.execute("INSERT OR REPLACE INTO relay VALUES (?,?,?)", (team_message_id, user_id, lead_id))

    def relay_target(self, team_message_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM relay WHERE team_message_id=?", (team_message_id,)).fetchone()

    # ---- статистика ----
    def stats(self, days: int) -> dict:
        since = time.time() - days * 86400
        q = lambda sql: self.conn.execute(sql, (since,)).fetchall()  # noqa: E731
        return {
            "starts": q("SELECT funnel, COUNT(*) n FROM events WHERE kind='start' AND at>=? GROUP BY funnel"),
            "leads": q("SELECT funnel, COUNT(*) n FROM leads WHERE created_at>=? GROUP BY funnel"),
            "sources": q("SELECT source, COUNT(*) n FROM leads WHERE created_at>=? GROUP BY source ORDER BY n DESC LIMIT 10"),
            "statuses": q("SELECT status, COUNT(*) n FROM leads WHERE created_at>=? GROUP BY status"),
        }
