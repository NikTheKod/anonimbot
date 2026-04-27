import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID
from database import init_db, save_pending, get_pending, delete_pending
from keyboards import main_menu, cancel_button, get_admin_keyboard, get_delete_keyboard

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния
class AskState(StatesGroup):
    waiting_for_text = State()

# ========== ОБРАБОТЧИКИ СООБЩЕНИЙ ==========

# Команда /start
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer(
        "🌟 **Добро пожаловать в Анонимный Чат!** 🌟\n\n"
        "Здесь ты можешь анонимно поделиться своими мыслями, вопросами или историями.\n"
        "Твоё сообщение уйдёт на модерацию, и после проверки появится в нашем канале.\n\n"
        "⬇️ **Выбери действие:**",
        parse_mode="Markdown",
        reply_markup=main_menu
    )

# Обработка кнопки "Правила"
@dp.message(F.text == "📜 Правила")
async def show_rules(message: types.Message):
    rules_text = (
        "📜 **Правила отправки анонимных сообщений:**\n\n"
        "1. ❌ **Запрещены оскорбления** — уважай других\n"
        "2. 🚫 **Запрещена реклама** — любые ссылки на сторонние ресурсы\n"
        "3. 💢 **Запрещены угрозы** — никакого насилия\n"
        "4. 📛 **Запрещён спам** — повторяющиеся сообщения\n"
        "5. 🔞 **Запрещён 18+ контент** — только безопасный контент\n\n"
        "⚠️ Нарушители будут заблокированы.\n"
        "✅ Администратор проверяет каждое сообщение перед публикацией."
    )
    await message.answer(rules_text, parse_mode="Markdown", reply_markup=main_menu)

# Обработка кнопки "О нас"
@dp.message(F.text == "ℹ️ О нас")
async def about_us(message: types.Message):
    about_text = (
        "ℹ️ **О проекте:**\n\n"
        "Этот бот создан для анонимного общения в нашем Telegram-канале.\n\n"
        "🤝 **Как это работает:**\n"
        "• Ты отправляешь сообщение через бота\n"
        "• Администратор проверяет его\n"
        "• После одобрения оно появляется в канале\n\n"
        "📌 **Важно:** Твои данные (имя, ID) остаются скрытыми.\n"
        "Администратор видит только текст сообщения.\n\n"
        "📢 **Наш канал:** [Присоединяйся!](https://t.me/ваш_канал)\n\n"
        "По вопросам: @ваш_админ"
    )
    await message.answer(about_text, parse_mode="Markdown", reply_markup=main_menu, disable_web_page_preview=True)

# Начало отправки сообщения
@dp.message(F.text == "📝 Отправить анонимное сообщение")
async def start_anonymous(message: types.Message, state: FSMContext):
    await state.set_state(AskState.waiting_for_text)
    await message.answer(
        "✏️ **Напиши своё анонимное сообщение**\n\n"
        "📏 Максимум 1000 символов\n"
        "📝 Можно использовать обычный текст или Markdown\n\n"
        "⚠️ Сообщение будет проверено администратором.\n"
        "🔞 Не нарушай правила — они выше.\n\n"
        "💡 *Чтобы отменить, нажми кнопку ниже*",
        parse_mode="Markdown",
        reply_markup=cancel_button
    )

# Отмена отправки
@dp.message(F.text == "❌ Отменить отправку")
async def cancel_anonymous(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "❌ **Отправка сообщения отменена**\n\n"
            "Ты можешь начать заново через главное меню.",
            parse_mode="Markdown",
            reply_markup=main_menu
        )
    else:
        await message.answer("🤔 У тебя нет активных действий для отмены.", reply_markup=main_menu)

# Обработка текста сообщения от пользователя
@dp.message(AskState.waiting_for_text, F.text)
async def process_anonymous_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_text = message.text.strip()

    # Проверка длины
    if len(user_text) > 1000:
        await message.answer(
            "❌ **Ошибка:** Сообщение слишком длинное!\n"
            f"📏 Максимум 1000 символов, у тебя {len(user_text)}\n"
            "✏️ Попробуй сократить и отправь заново.",
            parse_mode="Markdown"
        )
        return

    # Проверка на пустое сообщение
    if len(user_text) < 3:
        await message.answer(
            "❌ **Ошибка:** Сообщение слишком короткое!\n"
            "📏 Минимум 3 символа. Напиши что-то содержательное.",
            parse_mode="Markdown"
        )
        return

    # Отправляем уведомление пользователю
    status_msg = await message.answer(
        "⏳ **Отправляю сообщение на модерацию...**\n\n"
        "◦ Администратор рассмотрит его в ближайшее время\n"
        "◦ Ты получишь уведомление о решении",
        parse_mode="Markdown"
    )

    # Сохраняем в базу данных
    await save_pending(user_id, user_text, status_msg.message_id)

        # Отправляем админу на модерацию
    admin_text = (
        "📨 **НОВОЕ АНОНИМНОЕ СООБЩЕНИЕ**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{user_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 **Статистика:**\n"
        f"◦ Длина: {len(user_text)} символов\n"
        "◦ Отправитель: Аноним\n\n"
        "🔽 **Выбери действие:**"
    )

    await bot.send_message(
        ADMIN_ID,
        admin_text,
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard(status_msg.message_id)
    )

    # Обновляем сообщение пользователя с кнопкой "Удалить"
    await status_msg.edit_text(
        "✅ **Сообщение отправлено на модерацию!**\n\n"
        "◦ Администратор рассмотрит его в ближайшее время\n"
        "◦ Ты получишь уведомление о решении\n"
        "◦ Если передумал — можешь удалить обращение",
        parse_mode="Markdown",
        reply_markup=get_delete_keyboard(status_msg.message_id)
    )

    await state.clear()

# Если пользователь пишет что-то не то во время ожидания
@dp.message(AskState.waiting_for_text)
async def invalid_input(message: types.Message, state: FSMContext):
    await message.answer(
        "⚠️ **Пожалуйста, отправь текстовое сообщение**\n\n"
        "Стикеры, фото и другие медиафайлы не принимаются.\n"
        "Нажми «❌ Отменить отправку», чтобы вернуться в меню.",
        parse_mode="Markdown",
        reply_markup=cancel_button
    )

# ========== КНОПКА "УДАЛИТЬ ОБРАЩЕНИЕ" ==========

@dp.callback_query(F.data.startswith("delete_"))
async def delete_message(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_message_id = int(callback.data.split("_")[1])

    # Получаем данные из БД
    pending = await get_pending(bot_message_id)
    
    if not pending:
        await callback.answer("❌ Сообщение уже обработано или не найдено", show_alert=True)
        await callback.message.edit_text(
            "❌ **Ошибка:** Сообщение не найдено.\n"
            "Возможно, оно уже было обработано администратором.",
            parse_mode="Markdown"
        )
        return

    db_user_id, message_text = pending
    
    # Проверяем, что удаляет именно автор
    if user_id != db_user_id:
        await callback.answer("⛔ Это не твоё сообщение!", show_alert=True)
        return

    # Удаляем из БД
    await delete_pending(bot_message_id)
    
    # Уведомляем пользователя
    await callback.message.edit_text(
        "🗑 **Сообщение удалено**\n\n"
        "Твоё обращение было удалено из очереди.\n"
        "Если передумал — отправь заново через главное меню.",
        parse_mode="Markdown",
        reply_markup=main_menu
    )
    
        # Уведомляем админа (если сообщение ещё не обработано)
    await bot.send_message(
        ADMIN_ID,
        f"🗑 **Пользователь удалил обращение**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{message_text[:200]}...\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ Сообщение больше не требует модерации.",
        parse_mode="Markdown"
    )
    
    await callback.answer("✅ Сообщение удалено")

# ========== АДМИНСКИЕ КНОПКИ ==========

# Одобрить сообщение
@dp.callback_query(F.data.startswith("approve_"))
async def approve_message(callback: types.CallbackQuery):
    admin_id = callback.from_user.id

    # Проверка прав
    if admin_id != ADMIN_ID:
        await callback.answer("⛔ У вас нет прав для этого действия", show_alert=True)
        return

    bot_message_id = int(callback.data.split("_")[1])
    
    # Получаем данные из БД
    pending = await get_pending(bot_message_id)
    
    if not pending:
        await callback.answer("❌ Сообщение не найдено", show_alert=True)
        await callback.message.edit_text("❌ **Ошибка:** Сообщение уже было обработано или не найдено", parse_mode="Markdown")
        return

    user_id, message_text = pending

        # Форматируем сообщение для канала с красивым оформлением
    channel_message = (
        "🔒 **Анонимное сообщение**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{message_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ *Сообщение прислано анонимно*\n"
        "💭 *Администратор не видит отправителя*"
    )

    try:
        # Отправляем в канал
        await bot.send_message(
            CHANNEL_ID,
            channel_message,
            parse_mode="Markdown"
        )

                # Уведомляем пользователя об одобрении
        user_notification = (
            "✅ **Ваше сообщение опубликовано в канале!**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{message_text[:100]}{'...' if len(message_text) > 100 else ''}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💫 Спасибо, что делишься своими мыслями!"
        )
        
        await bot.send_message(
            user_id,
            user_notification,
            parse_mode="Markdown"
        )

        # Удаляем из БД
        await delete_pending(bot_message_id)

                # Обновляем сообщение у админа
        await callback.message.edit_text(
            f"✅ **ОПУБЛИКОВАНО В КАНАЛЕ**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{message_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Пользователь уведомлён\n"
            f"📢 Сообщение отправлено в канал",
            parse_mode="Markdown"
        )

        await callback.answer("✅ Сообщение опубликовано в канале")

    except Exception as e:
        await callback.answer("❌ Ошибка при публикации", show_alert=True)
        await callback.message.edit_text(
            f"❌ **Ошибка публикации:** {str(e)}\n\n"
            f"Проверь, что:\n"
            f"• Бот добавлен в канал как администратор\n"
            f"• CHANNEL_ID правильный\n"
            f"• У бота есть права на отправку сообщений",
            parse_mode="Markdown"
        )
        print(f"Error publishing: {e}")

# Отклонить сообщение
@dp.callback_query(F.data.startswith("reject_"))
async def reject_message(callback: types.CallbackQuery):
    admin_id = callback.from_user.id

    # Проверка прав
    if admin_id != ADMIN_ID:
        await callback.answer("⛔ У вас нет прав для этого действия", show_alert=True)
        return

    bot_message_id = int(callback.data.split("_")[1])
    
    # Получаем данные из БД
    pending = await get_pending(bot_message_id)
    
    if not pending:
        await callback.answer("❌ Сообщение не найдено", show_alert=True)
        await callback.message.edit_text("❌ **Ошибка:** Сообщение уже было обработано или не найдено", parse_mode="Markdown")
        return

    user_id, message_text = pending

        # Уведомляем пользователя об отказе
    reject_notification = (
        "❌ **Сообщение отклонено модератором**\n\n"
        "**Причины отклонения:**\n"
        "• Нарушение правил сообщества\n"
        "• Неподобающий контент\n"
        "• Реклама, спам или оскорбления\n\n"
        "📜 *Пожалуйста, ознакомься с правилами*\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{message_text[:200]}{'...' if len(message_text) > 200 else ''}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    await bot.send_message(
        user_id,
        reject_notification,
        parse_mode="Markdown"
    )

    # Удаляем из БД
    await delete_pending(bot_message_id)

        # Обновляем сообщение у админа
    await callback.message.edit_text(
        f"❌ **ОТКЛОНЕНО**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{message_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"❌ Пользователь уведомлён об отказе\n"
        f"📋 Причина: нарушение правил",
        parse_mode="Markdown"
    )

    await callback.answer("❌ Сообщение отклонено")

# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========

@dp.message(F.text == "/stats")
async def admin_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Только для администратора", reply_markup=main_menu)
        return

    from database import DB_PATH
    import aiosqlite
    
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM pending_messages") as cursor:
            count = await cursor.fetchone()
            await message.answer(
                f"📊 **Статистика бота**\n\n"
                f"◦ Сообщений в очереди: **{count[0]}**\n"
                f"◦ Админ: {'✅ настроен' if ADMIN_ID else '❌ не настроен'}\n"
                f"◦ Канал: {'✅ настроен' if CHANNEL_ID else '❌ не настроен'}\n\n"
                f"🟢 Бот работает исправно!",
                parse_mode="Markdown",
                reply_markup=main_menu
            )

# ========== ЗАПУСК БОТА ==========

async def main():
    # Инициализация базы данных
    await init_db()
    
    # Проверка переменных
    if not BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не задан!")
        return
    if not ADMIN_ID:
        print("❌ ОШИБКА: ADMIN_ID не задан!")
        return
    if not CHANNEL_ID:
        print("❌ ОШИБКА: CHANNEL_ID не задан!")
        return
    
    print("🤖 Бот запущен!")
    print(f"👤 Админ: {ADMIN_ID}")
    print(f"📢 Канал: {CHANNEL_ID}")
    print("✅ Готов к работе!")
    
    # Удаляем webhook и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
