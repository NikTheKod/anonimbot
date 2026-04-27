import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID
from database import init_db, save_pending, get_pending, delete_pending

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояния FSM
class AskState(StatesGroup):
    waiting_for_text = State()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для анонимных сообщений.\n\n"
        "Чтобы отправить анонимное сообщение в канал, используй команду /ask\n\n"
        "⚠️ Правила:\n"
        "• Запрещены оскорбления\n"
        "• Запрещена реклама\n"
        "• Запрещены угрозы\n"
        "• Нарушители будут заблокированы"
    )

# Команда /ask
@dp.message(Command("ask"))
async def cmd_ask(message: types.Message, state: FSMContext):
    await state.set_state(AskState.waiting_for_text)
    await message.answer(
        "📝 Напиши текст твоего анонимного сообщения.\n\n"
        "⚠️ Правила:\n"
        "• Без оскорблений\n"
        "• Без рекламы\n"
        "• Без спама\n"
        "• Без угроз\n\n"
        "Для отмены используй /cancel"
    )

# Обработка текста от пользователя
@dp.message(AskState.waiting_for_text, F.text)
async def process_anonymous_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_text = message.text.strip()
    
    if len(user_text) > 1000:
        await message.answer("❌ Сообщение слишком длинное (максимум 1000 символов)")
        return
    
    # Уведомление пользователя
    status_msg = await message.answer("⏳ Отправляю на модерацию...")
    
    # Кнопки для админа
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"approve_{status_msg.message_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{status_msg.message_id}")]
    ])
    
    # Сохраняем в БД
    await save_pending(user_id, user_text, status_msg.message_id)
    
    # Отправляем админу
    admin_text = f"📨 **НОВОЕ АНОНИМНОЕ СООБЩЕНИЕ**\n\n{user_text}\n\n━━━━━━━━━━━━━━━\nВыбери действие:"
    
    await bot.send_message(
        ADMIN_ID,
        admin_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await status_msg.edit_text("✅ Сообщение отправлено на модерацию. Админ рассмотрит его в ближайшее время.")

# Отмена
@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("🤔 Нет активных действий для отмены")
        return
    
    await state.clear()
    await message.answer("❌ Действие отменено")

# Любой другой текст во время ожидания
@dp.message(AskState.waiting_for_text)
async def process_invalid_input(message: types.Message, state: FSMContext):
    await message.answer("❌ Пожалуйста, отправь текст сообщения (текст, не фото, не стикер)\nДля отмены /cancel")

# Обработка кнопки "Опубликовать"
@dp.callback_query(F.data.startswith("approve_"))
async def approve_message(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Проверка что это админ
    if user_id != ADMIN_ID:
        await callback.answer("⛔ У вас нет прав для этого действия", show_alert=True)
        return
    
    # Получаем message_id из callback data
    bot_message_id = int(callback.data.split("_")[1])
    
    # Получаем данные из БД
    pending = await get_pending(bot_message_id)
    if not pending:
        await callback.answer("❌ Ошибка: сообщение не найдено", show_alert=True)
        await callback.message.edit_text("❌ Сообщение уже было обработано или не найдено")
        return
    
    user_id_sender, message_text = pending
    
    # Отправляем в канал
    try:
        channel_msg = await bot.send_message(
            CHANNEL_ID,
            f"🔒 **Анонимное сообщение**\n\n{message_text}",
            parse_mode="Markdown"
        )
        
        # Уведомляем пользователя
        await bot.send_message(
            user_id_sender,
            f"✅ **Сообщение опубликовано в канале!**\n\nВаше сообщение:\n{message_text[:200]}...",
            parse_mode="Markdown"
        )
        
        # Удаляем из БД
        await delete_pending(bot_message_id)
        
        # Обновляем сообщение админа
        await callback.message.edit_text(
            f"✅ **ОПУБЛИКОВАНО**\n\n{message_text}\n\n━━━━━━━━━━━━━━━\n✅ Сообщение опубликовано в канале",
            parse_mode="Markdown"
        )
        
        await callback.answer("✅ Опубликовано в канале")
        
    except Exception as e:
        await callback.answer("❌ Ошибка при публикации", show_alert=True)
        print(f"Error: {e}")

# Обработка кнопки "Отклонить"
@dp.callback_query(F.data.startswith("reject_"))
async def reject_message(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # Проверка что это админ
    if user_id != ADMIN_ID:
        await callback.answer("⛔ У вас нет прав для этого действия", show_alert=True)
        return
    
    # Получаем message_id из callback data
    bot_message_id = int(callback.data.split("_")[1])
    
    # Получаем данные из БД
    pending = await get_pending(bot_message_id)
    if not pending:
        await callback.answer("❌ Ошибка: сообщение не найдено", show_alert=True)
        await callback.message.edit_text("❌ Сообщение уже было обработано или не найдено")
        return
    
    user_id_sender, message_text = pending
    
    # Уведомляем пользователя об отказе
    await bot.send_message(
        user_id_sender,
        f"❌ **Сообщение отклонено модератором**\n\n"
        f"Причина: нарушение правил (запрещены оскорбления, реклама, спам или угрозы)\n\n"
        f"Ваше сообщение:\n{message_text[:200]}...",
        parse_mode="Markdown"
    )
    
    # Удаляем из БД
    await delete_pending(bot_message_id)
    
    # Обновляем сообщение админа
    await callback.message.edit_text(
        f"❌ **ОТКЛОНЕНО**\n\n{message_text}\n\n━━━━━━━━━━━━━━━\n❌ Сообщение отклонено\n✅ Пользователь уведомлен",
        parse_mode="Markdown"
    )
    
    await callback.answer("❌ Сообщение отклонено")

# Команда /stats (только для админа)
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Только для админа")
        return
    
    from database import DB_PATH
    import aiosqlite
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM pending_messages") as cursor:
            count = await cursor.fetchone()
            await message.answer(f"📊 Статистика:\n\nВ очереди на модерацию: {count[0]} сообщений")

# Запуск бота
async def main():
    # Инициализация базы данных
    await init_db()
    
    # Запуск бота
    print("🤖 Бот запущен!")
    print(f"👤 Админ: {ADMIN_ID}")
    print(f"📢 Канал: {CHANNEL_ID}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
