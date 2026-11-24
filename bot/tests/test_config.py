"""Тесты config.py: переменные окружения, ADMIN_ID, путь к базе."""
import importlib
import os


def test_bot_token_from_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    import config
    importlib.reload(config)
    assert config.BOT_TOKEN == "test-token"


def test_admin_id_default_3588541(monkeypatch):
    monkeypatch.delenv("ADMIN_ID", raising=False)
    import config
    importlib.reload(config)
    assert config.ADMIN_ID == 3588541


def test_db_path_named_runes_db():
    import config
    importlib.reload(config)
    assert config.DB_PATH.name == "runes.db"
    assert config.DB_PATH.parent.exists()
