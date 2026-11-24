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
