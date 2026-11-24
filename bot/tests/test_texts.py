"""Тесты texts.py — сообщения расклада (Task 5)."""
import runes


def _drawn():
    positions = ("past", "present", "future")
    out = []
    for rid, pos in zip((1, 2, 3), positions):
        rune = next(r for r in runes.RUNES if r["id"] == rid)
        out.append({"rune": rune, "position": pos, "is_reversed": False})
    return out


def test_result_message_contains_all_positions():
    import texts
    msg = texts.result_message(_drawn())
    for s in ("✦ Послание Рун", "Прошлое", "Настоящее", "Будущее",
              "Руны указывают путь", "24 руны"):
        assert s in msg, s
    for item in _drawn():
        assert item["rune"]["nameRu"] in msg


def test_result_message_within_telegram_limit():
    import texts

    def longest(pos):
        return max(runes.RUNES, key=lambda r: len(r[pos]))

    drawn = [
        {"rune": longest("past"), "position": "past", "is_reversed": False},
        {"rune": longest("present"), "position": "present", "is_reversed": False},
        {"rune": longest("future"), "position": "future", "is_reversed": False},
    ]
    assert len(texts.result_message(drawn)) <= 4096


def test_reveal_message_has_no_interpretation():
    import texts
    rune = runes.RUNES[0]  # Феху: «В прошлом вы обладали ресурсами…»
    msg = texts.reveal_message(rune, "past", False)
    assert rune["past"][:20] not in msg
    assert rune["symbol"] in msg
    assert rune["nameRu"] in msg
    assert "Прямая позиция" in msg


def test_draw_prompt_per_position():
    import texts
    assert "первую" in texts.draw_prompt("past")
    assert "вторую" in texts.draw_prompt("present")
    assert "третью" in texts.draw_prompt("future")


# --- Task 3: лимиты и Stars ----------------------------------------------

def test_limit_reached_message():
    import texts
    assert "2 расклада" in texts.LIMIT_REACHED
    assert "30 звёзд" in texts.LIMIT_REACHED


def test_premium_activated_contains_date():
    import datetime
    import time

    import texts
    until = int(time.time()) + 7 * 86400
    msg = texts.premium_activated(until)
    assert "безлимит" in msg.lower()
    expect_date = datetime.datetime.fromtimestamp(until).strftime("%d.%m")
    assert expect_date in msg


def test_after_draw_hint_pluralization():
    import texts

    h = texts.after_draw_hint(1)
    assert "1 расклад" in h and "расклада" not in h and "раскладов" not in h

    h = texts.after_draw_hint(2)
    assert "2 расклада" in h and "раскладов" not in h

    assert "5 раскладов" in texts.after_draw_hint(5)

    h = texts.after_draw_hint(21)
    assert "21 расклад" in h and "раскладов" not in h

    assert "0 раскладов" in texts.after_draw_hint(0)
