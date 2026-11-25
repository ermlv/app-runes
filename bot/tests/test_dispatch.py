"""Диспетчер-тесты: поведение хендлеров через dp.feed_update.

Перехватывает bot.session.make_request — весь API-трафик бота идёт через
сессию. Покрывает проход исправлений финального ревью ветки:
C1 — сериализация обработки апдейтов (гонка в draw_pull с sleep(1.5));
I2 — кнопки меню/свободный текст отвечают и во время расклада.
Плюс pin-тест поведения «Кнопка устарела» (закреплено чек-листом владельца).
"""
import asyncio
from datetime import datetime, timezone

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Chat, Message, Update, User

import bot as bot_module  # noqa: F401  (окружение: конфиг, токен из .env)

# Импорт bot.py устанавливает подмену DNS из TG_API_IP — снимаем сразу,
# чтобы не влиять на другие тесты (test_tgip ждёт оригинальный резолвер).
import tgip
tgip.uninstall()


class Recorder:
    """Перехватывает API-вызовы бота и записывает тексты."""

    def __init__(self, monkeypatch):
        self.sent = []
        self.answered = []
        self.markups = []  # reply_markup каждого отправленного сообщения
        self.photos = []   # SendPhoto: {caption, has_photo}

        async def fake_request(b, method, timeout=None):
            name = type(method).__name__
            if name == "SendMessage":
                self.sent.append(method.text)
                self.markups.append(getattr(method, "reply_markup", None))
            elif name == "AnswerCallbackQuery":
                self.answered.append(getattr(method, "text", None))
            elif name == "SendPhoto":
                self.photos.append({
                    "caption": method.caption,
                    "has_photo": method.photo is not None,
                    "markup": getattr(method, "reply_markup", None),
                })
            return None

        monkeypatch.setattr(bot_module.bot.session, "make_request", fake_request)


def _markup_callbacks(markup):
    if markup is None:
        return []
    return [btn.callback_data for row in markup.inline_keyboard for btn in row]


def _fresh_db(tmp_path, monkeypatch):
    """Чистая БД на тест: handlers читают config.DB_PATH при каждом соединении."""
    import config
    import db
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "dispatch.db")
    db.init_db()
    return db


def _key():
    return StorageKey(bot_id=int(bot_module.bot.token.split(":")[0]),
                      chat_id=1, user_id=1)


def _ctx():
    return FSMContext(storage=bot_module.dp.storage, key=_key())


def _message(text):
    return Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=1, is_bot=False, first_name="Тест"),
        text=text,
    )


def _callback(data):
    return CallbackQuery(
        id="777",
        chat_instance="ci",
        from_user=User(id=1, is_bot=False, first_name="Тест"),
        message=_message(None),
        data=data,
    )


async def _feed_text(text):
    await bot_module.dp.feed_update(
        bot=bot_module.bot,
        update=Update(update_id=1, message=_message(text)),
    )


async def _feed_callback(data):
    await bot_module.dp.feed_update(
        bot=bot_module.bot,
        update=Update(update_id=1, callback_query=_callback(data)),
    )


# ----------------------------------------------------------------- I2
def test_menu_info_answers_mid_draw(monkeypatch):
    rec = Recorder(monkeypatch)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await ctx.set_state(bot_module.DrawSG.drawing)
        await _feed_text("ℹ️ Что за расклад")

    asyncio.run(scenario())
    assert rec.sent, "бот молчит на видимую кнопку «ℹ️ Что за расклад» mid-draw"
    assert "Расклад «Три Норны»" in rec.sent[0]


def test_menu_draw_restarts_mid_draw(monkeypatch):
    rec = Recorder(monkeypatch)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await ctx.set_state(bot_module.DrawSG.drawing)
        await ctx.update_data(
            drawn=[{"rune": {"id": 5}, "position": "future",
                    "is_reversed": False}],
            pos="future",
        )
        await _feed_text("🔮 Расклад Три Норны")
        return await ctx.get_data()

    data = asyncio.run(scenario())
    assert rec.sent, "бот молчит на кнопку «🔮 Расклад Три Норны» mid-draw"
    assert "Вытяните" in rec.sent[0]
    assert data["drawn"] == [] and data["pos"] == "past", \
        f"расклад не перезапустился: {data}"


def test_free_text_hint_mid_draw(monkeypatch):
    rec = Recorder(monkeypatch)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await ctx.set_state(bot_module.DrawSG.drawing)
        await _feed_text("а что это вообще такое?")

    asyncio.run(scenario())
    assert rec.sent, "бот молчит на свободный текст mid-draw"
    assert "Выберите действие" in rec.sent[0]


# ----------------------------------------------------------------- C1
def test_main_serializes_updates(monkeypatch):
    captured = {}

    async def fake_webhook(**kwargs):
        return None

    async def fake_polling(b, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(bot_module.bot, "delete_webhook", fake_webhook)
    monkeypatch.setattr(bot_module.dp, "start_polling", fake_polling)

    asyncio.run(bot_module.main())
    assert captured.get("tasks_concurrency_limit") == 1, \
        "start_polling без tasks_concurrency_limit=1 — гонка в draw_pull"


# ------------------------------------- pin: поведение, подтверждённое чек-листом
def test_stale_pull_answers_устарела(monkeypatch):
    """Кнопка «Вытянуть» без состояния расклада (после результата/рестарта)
    отвечает «Кнопка устарела» + меню — закреплено чек-листом владельца и
    разрешённым в журнале расхождением спеки (строка «перезапускает»)."""
    rec = Recorder(monkeypatch)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await _feed_callback("draw:pull")
        return await ctx.get_state()

    state = asyncio.run(scenario())
    assert rec.answered == ["Кнопка устарела"], rec.answered
    assert rec.sent and "меню" in rec.sent[0].lower(), rec.sent
    assert state is None, "старая кнопка не должна начинать новый расклад"


# ------------------------------------------- Task 4: гейт лимита и подсказка
def _fill_quota(db, n_draws, premium_until=0):
    for _ in range(n_draws):
        db.add_draw(1, "[]")
    if premium_until:
        db.set_premium_until(1, premium_until)


def test_menu_draw_blocked_when_limit_reached(monkeypatch, tmp_path):
    rec = Recorder(monkeypatch)
    db = _fresh_db(tmp_path, monkeypatch)
    _fill_quota(db, 2)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await _feed_text("🔮 Расклад Три Норны")
        return await ctx.get_state()

    state = asyncio.run(scenario())
    assert rec.sent, "нет ответа при исчерпанном лимите"
    assert "2 расклада" in rec.sent[0], rec.sent[0]
    assert any("pay:stars" in _markup_callbacks(m) for m in rec.markups), \
        "нет кнопки покупки в лимит-сообщении"
    assert not any("Вытяните" in s for s in rec.sent), \
        "расклад стартовал при исчерпанном лимите"
    assert state is None, "состояние расклада не должно устанавливаться"


def test_again_blocked_when_limit_reached(monkeypatch, tmp_path):
    """Review Focus №3: «Всё равно гадать» после Фреи не должен обходить лимит."""
    rec = Recorder(monkeypatch)
    db = _fresh_db(tmp_path, monkeypatch)
    _fill_quota(db, 2)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await ctx.set_state(bot_module.DrawSG.drawing)  # расклад «идёт»
        await _feed_callback("draw:again")

    asyncio.run(scenario())
    assert any("2 расклада" in s for s in rec.sent), rec.sent
    assert not any("Вытяните" in s for s in rec.sent), \
        "draw:again обошёл лимит"


def test_menu_draw_starts_when_premium(monkeypatch, tmp_path):
    rec = Recorder(monkeypatch)
    db = _fresh_db(tmp_path, monkeypatch)
    import time as _time
    _fill_quota(db, 2, premium_until=int(_time.time()) + 1000)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await _feed_text("🔮 Расклад Три Норны")
        return await ctx.get_state()

    state = asyncio.run(scenario())
    assert rec.sent and "Вытяните" in rec.sent[0], rec.sent
    assert state == bot_module.DrawSG.drawing.state


def test_menu_draw_starts_when_quota_left(monkeypatch, tmp_path):
    rec = Recorder(monkeypatch)
    db = _fresh_db(tmp_path, monkeypatch)
    _fill_quota(db, 1)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await _feed_text("🔮 Расклад Три Норны")
        return await ctx.get_state()

    state = asyncio.run(scenario())
    assert rec.sent and "Вытяните" in rec.sent[0], rec.sent
    assert state == bot_module.DrawSG.drawing.state


def test_after_draw_hint_on_completion(monkeypatch, tmp_path):
    """После завершения расклада — подсказка об остатке (0 draws в БД,
    в state вытянуты2 → после завершения1 → «Осталось1 расклад»)."""
    import time as _time

    import runes as runes_mod

    rec = Recorder(monkeypatch)
    _fresh_db(tmp_path, monkeypatch)

    async def _noop(*args, **kwargs):
        return None
    monkeypatch.setattr(bot_module.asyncio, "sleep", _noop)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await ctx.set_state(bot_module.DrawSG.drawing)
        await ctx.update_data(
            drawn=[{"rune": runes_mod.RUNES[0], "position": "past",
                    "is_reversed": False},
                   {"rune": runes_mod.RUNES[1], "position": "present",
                    "is_reversed": False}],
            pos="future",
        )
        await _feed_callback("draw:pull")
        return await ctx.get_state()

    state = asyncio.run(scenario())
    hints = [s for s in rec.sent if "Осталось" in s]
    assert hints, f"нет подсказки об остатке; sent={rec.sent}"
    assert "1 расклад" in hints[-1] and "раскладов" not in hints[-1], hints[-1]
    assert state is None, "состояние должно очиститься после итога"


# ------------------------------------- картинка «Предостережение Фрейи»
def test_new_draw_sends_freya_photo(monkeypatch, tmp_path):
    """«✦ Новое гадание ✦» → Фрейя уходит картинкой с текстом в подписи."""
    rec = Recorder(monkeypatch)
    _fresh_db(tmp_path, monkeypatch)

    async def scenario():
        await _ctx().clear()
        await _feed_callback("draw:new")

    asyncio.run(scenario())
    assert rec.photos, "предупреждение Фреи ушло без картинки"
    cap = rec.photos[0]["caption"] or ""
    assert rec.photos[0]["has_photo"], "SendPhoto без файла"
    assert "Предостережение Фрейи" in cap, cap[:80]
    assert "Остановись" in cap, cap[:80]
    # кнопки «Понятно, подожду» / «Всё равно гадать» обязаны остаться
    assert _markup_callbacks(rec.photos[0]["markup"]) == ["draw:cancel", "draw:again"], \
        rec.photos[0]["markup"]


# --------------------------------------- картинки рун при раскрытии
def test_reveal_sends_rune_photo(monkeypatch, tmp_path):
    """Раскрытие руны уходит фото тайла с текстом в подписи."""
    rec = Recorder(monkeypatch)
    _fresh_db(tmp_path, monkeypatch)

    async def _noop(*args, **kwargs):
        return None
    monkeypatch.setattr(bot_module.asyncio, "sleep", _noop)

    async def scenario():
        ctx = _ctx()
        await ctx.clear()
        await ctx.set_state(bot_module.DrawSG.drawing)
        await ctx.update_data(drawn=[], pos="past")
        await _feed_callback("draw:pull")

    asyncio.run(scenario())
    assert rec.photos, "раскрытие ушло без фото руны"
    cap = rec.photos[0]["caption"] or ""
    assert "Позиция" in cap or "позиция" in cap or "Прямая" in cap or "Перевёрнутая" in cap, cap
    assert rec.photos[0]["has_photo"], "SendPhoto без файла"


def test_rune_photo_rotation():
    """Перевёрнутая руна — то же изображение, повёрнутое на180°."""
    import io as _io

    from PIL import Image

    direct = bot_module.rune_photo(1, False).data
    flipped = bot_module.rune_photo(1, True).data
    assert direct != flipped, "перевёрнутая не отличается от прямой"

    a = Image.open(_io.BytesIO(direct))
    b = Image.open(_io.BytesIO(flipped))
    assert a.size == b.size
    # левый верхний угол прямого == правый нижний повёрнутого
    assert a.getpixel((0, 0)) == b.getpixel((b.size[0] - 1, b.size[1] - 1)), \
        "изображение не повёрнуто на180°"
