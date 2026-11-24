"""Диспетчер-тесты платежей Telegram Stars (Task 5).

Перехватывает bot.session.make_request (весь API-трафик бота).
"""
import asyncio
import time
from datetime import datetime, timezone

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import (CallbackQuery, Chat, Message, PreCheckoutQuery,
                           SuccessfulPayment, Update, User)

import bot as bot_module  # noqa: F401

# Импорт bot.py устанавливает подмену DNS из TG_API_IP — снимаем сразу.
import tgip
tgip.uninstall()

WEEK = 7 * 86400


class Recorder:
    def __init__(self, monkeypatch):
        self.sent = []
        self.answered = []
        self.markups = []
        self.invoices = []       # {currency, amount, title}
        self.pre_checkout = []   # {ok, error_message}

        async def fake_request(b, method, timeout=None):
            name = type(method).__name__
            if name == "SendMessage":
                self.sent.append(method.text)
                self.markups.append(getattr(method, "reply_markup", None))
            elif name == "AnswerCallbackQuery":
                self.answered.append(getattr(method, "text", None))
            elif name == "SendInvoice":
                self.invoices.append({
                    "currency": method.currency,
                    "amount": method.prices[0].amount,
                    "title": method.title,
                })
            elif name == "AnswerPreCheckoutQuery":
                self.pre_checkout.append({
                    "ok": method.ok,
                    "error_message": method.error_message,
                })
            return None

        monkeypatch.setattr(bot_module.bot.session, "make_request", fake_request)


def _key():
    return StorageKey(bot_id=int(bot_module.bot.token.split(":")[0]),
                      chat_id=1, user_id=1)


def _ctx():
    return FSMContext(storage=bot_module.dp.storage, key=_key())


def _message(text=None):
    return Message(
        message_id=1,
        date=datetime.now(timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=1, is_bot=False, first_name="Тест"),
        text=text,
    )


def _pre_checkout(currency="XTR", total_amount=30, payload="1"):
    return PreCheckoutQuery(
        id="pcq1",
        from_user=User(id=1, is_bot=False, first_name="Тест"),
        currency=currency,
        total_amount=total_amount,
        invoice_payload=payload,
    )


def _payment_message(charge_id="ch1", amount=30, payload="1"):
    return Message(
        message_id=50,
        date=datetime.now(timezone.utc),
        chat=Chat(id=1, type="private"),
        from_user=User(id=1, is_bot=False, first_name="Тест"),
        successful_payment=SuccessfulPayment(
            currency="XTR",
            total_amount=amount,
            invoice_payload=payload,
            telegram_payment_charge_id=charge_id,
            provider_payment_charge_id="",
        ),
    )


async def _feed_text(text):
    await bot_module.dp.feed_update(
        bot=bot_module.bot,
        update=Update(update_id=1, message=_message(text)),
    )


async def _feed_callback(data):
    cq = CallbackQuery(
        id="777",
        chat_instance="ci",
        from_user=User(id=1, is_bot=False, first_name="Тест"),
        message=_message(None),
        data=data,
    )
    await bot_module.dp.feed_update(
        bot=bot_module.bot,
        update=Update(update_id=1, callback_query=cq),
    )


async def _feed(update):
    await bot_module.dp.feed_update(bot=bot_module.bot, update=update)


def _fresh_db(tmp_path, monkeypatch):
    import config
    import db
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "pay.db")
    db.init_db()
    return db


def _fill_quota(db, n_draws):
    for _ in range(n_draws):
        db.add_draw(1, "[]")


# ----------------------------------------------------------------- инвойс
def test_buy_button_sends_xtr_invoice(monkeypatch, tmp_path):
    rec = Recorder(monkeypatch)
    db = _fresh_db(tmp_path, monkeypatch)
    _fill_quota(db, 2)

    async def scenario():
        await _ctx().clear()
        await _feed_text("🔮 Расклад Три Норны")   # → LIMIT_REACHED
        await _feed_callback("pay:stars")

    asyncio.run(scenario())
    assert rec.invoices, "кнопка покупки не отправила инвойс"
    inv = rec.invoices[0]
    assert inv["currency"] == "XTR", inv
    assert inv["amount"] == 30, inv
    assert "Безлимит" in inv["title"], inv


# ----------------------------------------------------------- pre_checkout
def test_pre_checkout_ok_for_valid(monkeypatch, tmp_path):
    rec = Recorder(monkeypatch)
    _fresh_db(tmp_path, monkeypatch)

    async def scenario():
        await _feed(Update(update_id=1, pre_checkout_query=_pre_checkout()))

    asyncio.run(scenario())
    assert rec.pre_checkout and rec.pre_checkout[0]["ok"] is True, rec.pre_checkout


def test_pre_checkout_rejected_for_wrong_amount(monkeypatch, tmp_path):
    rec = Recorder(monkeypatch)
    _fresh_db(tmp_path, monkeypatch)

    async def scenario():
        await _feed(Update(
            update_id=1,
            pre_checkout_query=_pre_checkout(total_amount=25),
        ))

    asyncio.run(scenario())
    assert rec.pre_checkout and rec.pre_checkout[0]["ok"] is False, rec.pre_checkout
    assert rec.pre_checkout[0]["error_message"], "нет сообщения об ошибке"


# ----------------------------------------------------- successful_payment
def test_successful_payment_sets_premium(monkeypatch, tmp_path):
    rec = Recorder(monkeypatch)
    db = _fresh_db(tmp_path, monkeypatch)

    async def scenario():
        await _feed(Update(update_id=1, message=_payment_message()))
        return db.get_premium_until(1)

    until = asyncio.run(scenario())
    now = int(time.time())
    assert now + WEEK - 5 <= until <= now + WEEK + 5, until
    assert any("безлимит" in s.lower() for s in rec.sent), rec.sent


def test_successful_payment_not_extended_twice(monkeypatch, tmp_path):
    """Review Focus №2: повторная доставка того же charge_id не продлевает."""
    rec = Recorder(monkeypatch)
    db = _fresh_db(tmp_path, monkeypatch)

    async def scenario():
        await _feed(Update(update_id=1, message=_payment_message("chX")))
        first = db.get_premium_until(1)
        await _feed(Update(update_id=1, message=_payment_message("chX")))
        return first, db.get_premium_until(1)

    first, second = asyncio.run(scenario())
    assert first > 0
    assert second == first, f"премиум продлён повторной доставкой: {first} → {second}"


# ------------------------------------------------------------ main() режим
def test_main_keeps_pending_updates(monkeypatch, tmp_path):
    """Review Focus №1: рестарт не выбрасывает pending successful_payment."""
    captured = {"webhook": {}, "polling": {}}

    async def fake_webhook(**kwargs):
        captured["webhook"] = kwargs

    async def fake_polling(b, **kwargs):
        captured["polling"] = kwargs

    monkeypatch.setattr(bot_module.bot, "delete_webhook", fake_webhook)
    monkeypatch.setattr(bot_module.dp, "start_polling", fake_polling)

    asyncio.run(bot_module.main())
    assert captured["webhook"].get("drop_pending_updates") is False, \
        "drop_pending_updates=True выбросил бы оплаты при рестарте"
    assert captured["polling"].get("tasks_concurrency_limit") == 1, \
        "сериализация обработки апдейтов потеряна"
