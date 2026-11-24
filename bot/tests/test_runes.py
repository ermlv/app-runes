"""Тесты логики расклада — bot/runes.py (Task 4)."""
import random

import pytest


def test_draw_rune_excludes_previous():
    import runes
    random.seed(42)
    exclude = []
    drawn_ids = []
    for _ in range(3):
        rune, _is_reversed = runes.draw_rune(exclude)
        assert rune["id"] not in exclude
        drawn_ids.append(rune["id"])
        exclude = exclude + [rune["id"]]
    assert len(set(drawn_ids)) == 3


def test_reversed_only_when_flagged(monkeypatch):
    import runes
    monkeypatch.setattr(runes.random, "random", lambda: 0.0)
    plain = next(r for r in runes.RUNES if not r.get("reversed"))
    flagged = next(r for r in runes.RUNES if r.get("reversed"))

    _, is_reversed = runes.draw_rune([r["id"] for r in runes.RUNES if r["id"] != plain["id"]])
    assert is_reversed is False

    _, is_reversed = runes.draw_rune([r["id"] for r in runes.RUNES if r["id"] != flagged["id"]])
    assert is_reversed is True


def test_reversed_never_on_30_percent(monkeypatch):
    import runes
    monkeypatch.setattr(runes.random, "random", lambda: 0.31)
    flagged = next(r for r in runes.RUNES if r.get("reversed"))
    _, is_reversed = runes.draw_rune([r["id"] for r in runes.RUNES if r["id"] != flagged["id"]])
    assert is_reversed is False


def test_reversed_text_falls_back_to_plain():
    import runes
    without_field = {"id": 1, "reversed": True, "present": "обычный текст"}
    assert runes.rune_text(without_field, "present", True) == "обычный текст"

    with_field = next(r for r in runes.RUNES if r.get("reversedPresent"))
    assert runes.rune_text(with_field, "present", True) == with_field["reversedPresent"]
    assert runes.rune_text(with_field, "present", False) == with_field["present"]


def test_draw_rune_raises_when_exhausted():
    import runes
    with pytest.raises(ValueError):
        runes.draw_rune(list(range(1, 25)))
