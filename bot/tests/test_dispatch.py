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

        async def fake_request(b, method, timeout=None):
            name = type(method).__name__
            if name == "SendMessage":
                self.sent.append(method.text)
            elif name == "AnswerCallbackQuery":
                self.answered.append(getattr(method, "text", None))
            return None

        monkeypatch.setattr(bot_module.bot.session, "make_request", fake_request)


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
