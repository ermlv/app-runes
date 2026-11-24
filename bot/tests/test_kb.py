"""Тесты kb.py — клавиатуры и callback-контракт с bot.py (Task 6)."""


def _inline_callbacks(markup):
    return [btn.callback_data for row in markup.inline_keyboard for btn in row]


def test_menu_two_buttons_in_order():
    import kb
    texts = [btn.text for row in kb.MENU.keyboard for btn in row]
    assert texts == ["🔮 Расклад Три Норны", "ℹ️ Что за расклад"]


def test_pull_kb_callback_and_text():
    import kb
    assert _inline_callbacks(kb.pull_kb("past")) == ["draw:pull"]
    assert "вторую" in kb.pull_kb("present").inline_keyboard[0][0].text
    assert _inline_callbacks(kb.pull_kb("present")) == ["draw:pull"]
    assert _inline_callbacks(kb.pull_kb("future")) == ["draw:pull"]


def test_result_callbacks():
    import kb
    assert _inline_callbacks(kb.RESULT) == ["draw:new", "menu"]


def test_freya_callbacks():
    import kb
    assert _inline_callbacks(kb.FREYA) == ["draw:cancel", "draw:again"]


def test_buy_premium_callback():
    import kb
    assert _inline_callbacks(kb.BUY_PREMIUM) == ["pay:stars"]
    assert "30 звёзд" in kb.BUY_PREMIUM.inline_keyboard[0][0].text
