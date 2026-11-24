"""Тесты bot/runes.json — экспорта из src/data/runes.ts (Task 3)."""
import json
from pathlib import Path

RUNES_JSON = Path(__file__).resolve().parents[1] / "runes.json"


def _load():
    return json.loads(RUNES_JSON.read_text(encoding="utf-8"))


def test_24_unique_ids_1_to_24():
    runes = _load()
    assert len(runes) == 24
    ids = [r["id"] for r in runes]
    assert sorted(ids) == list(range(1, 25))


def test_required_fields_nonempty():
    for r in _load():
        for key in ("name", "nameRu", "symbol", "meaning", "past", "present", "future"):
            assert isinstance(r[key], str) and r[key].strip(), (r["id"], key)


def test_reversed_fields():
    for r in _load():
        if r.get("reversed") is True:
            assert r.get("reversedMeaning", "").strip(), r["id"]
        for key, value in r.items():
            if key.startswith("reversed") and key != "reversed":
                assert isinstance(value, str) and value.strip(), (r["id"], key)
