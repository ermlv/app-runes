"""Тесты db.py: users, draws, stats (Task 2)."""
import config


def _ready(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    import db
    db.init_db()
    return db


def test_init_db_idempotent(tmp_path, monkeypatch):
    db = _ready(tmp_path, monkeypatch)
    db.init_db()  # второй вызов подряд — без ошибок


def test_upsert_user_dedupes(tmp_path, monkeypatch):
    db = _ready(tmp_path, monkeypatch)
    db.upsert_user(1, "alice", "Алиса")
    db.upsert_user(1, "alice", "Алиса")
    assert db.stats()["users"] == 1


def test_add_draw_counts(tmp_path, monkeypatch):
    db = _ready(tmp_path, monkeypatch)
    draw_id = db.add_draw(1, "[]")
    assert isinstance(draw_id, int)
    assert db.stats()["draws"] == 1


# --- Task 2: лимиты, премиум, покупки ------------------------------------

WEEK = 7 * 86400


def test_migration_adds_premium_until_to_existing_table(tmp_path, monkeypatch):
    import sqlite3
    import config
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE TABLE users (
               user_id    INTEGER PRIMARY KEY,
               username   TEXT DEFAULT '',
               first_name TEXT DEFAULT '',
               created_at INTEGER NOT NULL
           )"""
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(config, "DB_PATH", db_path)
    import db
    db.init_db()  # миграция на существующей схеме

    conn = sqlite3.connect(str(db_path))
    cols = [r[1] for r in conn.execute("pragma table_info(users)")]
    conn.close()
    assert "premium_until" in cols, "миграция не добавила premium_until"

    db.init_db()  # повторный вызов — не падает


def test_count_recent_draws_window_edge(tmp_path, monkeypatch):
    import sqlite3
    import time

    import config
    db = _ready(tmp_path, monkeypatch)
    now = int(time.time())
    conn = sqlite3.connect(str(config.DB_PATH))
    for uid, ts in ((1, now - WEEK), (1, now - WEEK + 1), (1, now), (2, now)):
        conn.execute("INSERT INTO draws (user_id, runes, created_at) VALUES (?, '[]', ?)",
                     (uid, ts))
    conn.commit()
    conn.close()
    # граница now-WEEK включена НЕ должна (строго > since)
    assert db.count_recent_draws(1, now - WEEK) == 2
    assert db.count_recent_draws(2, now - WEEK) == 1
    assert db.count_recent_draws(3, now - WEEK) == 0


def test_set_get_premium_until(tmp_path, monkeypatch):
    db = _ready(tmp_path, monkeypatch)
    db.set_premium_until(1, 12345)
    assert db.get_premium_until(1) == 12345
    assert db.get_premium_until(999) == 0  # нет строки


def test_apply_purchase_deduplicates(tmp_path, monkeypatch):
    """Одна операция = и покупка, и премиум (атомарный контракт) + дедуп."""
    import time as _time

    db = _ready(tmp_path, monkeypatch)
    now = int(_time.time())

    until = db.apply_purchase("ch1", 1, 30, now)
    assert until == now + 7 * 86400, until
    assert db.get_premium_until(1) == until, "премиум не выдан той же операцией"
    assert db.apply_purchase("ch1", 1, 30, now) is None, "дубль charge_id"
    assert db.get_premium_until(1) == until, "дубль продлил премиум"
    # вторая покупка (другой charge_id) продлевает от текущего срока
    until2 = db.apply_purchase("ch2", 1, 30, until)
    assert until2 == until + 7 * 86400, until2
