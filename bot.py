import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ========== ПОЛУЧАЕМ ПЕРЕМЕННЫЕ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# ========== ПРОВЕРКА (ТОЛЬКО ПРИ ЗАПУСКЕ) ==========
if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не найден")
    sys.exit(1)
if not ADMIN_ID:
    print("❌ Ошибка: ADMIN_ID не найден")
    sys.exit(1)
if not CHANNEL_ID:
    print("❌ Ошибка: CHANNEL_ID не найден")
    sys.exit(1)

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    print(f"❌ ADMIN_ID должен быть числом: {ADMIN_ID}")
    sys.exit(1)

print(f"✅ Переменные загружены")
print(f"   ADMIN_ID: {ADMIN_ID}")
print(f"   CHANNEL_ID: {CHANNEL_ID}")

# ========== СОСТОЯНИЯ ==========
class QuestionStates(StatesGroup):
    waiting_for_question = State()

# ========== КЛАВИАТУРЫ ==========
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📝 Задать анонимный вопрос")]],
    resize_keyboard=True
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отменить")]],
    resize_keyboard=True
)

def admin_buttons(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить в канал", callback_data=f"approve_{user_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")]
        ]
    )

# ========== РОУТЕР ==========
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 <b>Анонимный бот вопросов</b>\n\n"
        "📌 <b>Правила:</b>\n"
        "• Запрещены оскорбления и мат\n"
        "• Запрещена реклама\n"
        "• Запрещена личная информация\n\n"
        "👇 Нажмите кнопку ниже чтобы задать вопрос",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )

@router.message(F.text == "📝 Задать анонимный вопрос")
async def ask_question(message: Message, state: FSMContext):
    await state.set_state(QuestionStates.waiting_for_question)
    await message.answer(
        "📝 <b>Напишите текст вашего вопроса</b>\n\n"
        "❌ Для отмены нажмите кнопку Отменить",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )

@router.message(QuestionStates.waiting_for_question, F.text)
async def process_question(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Отправка вопроса отменена", reply_markup=main_keyboard)
        return
    
    question_text = message.text
    user_id = message.from_user.id
    
    # Отправляем админу на модерацию
    await bot.send_message(
        ADMIN_ID,
        f"🆕 <b>НОВЫЙ ВОПРОС</b>\n\n"
        f"От пользователя: <code>{user_id}</code>\n"
        f"Текст: {question_text}",
        reply_markup=admin_buttons(user_id),
        parse_mode="HTML"
    )
    
    await message.answer(
        "✅ Ваш вопрос отправлен на модерацию!\n"
        "Администратор проверит его и опубликует.",
        reply_markup=main_keyboard
    )
    await state.clear()

@router.message(QuestionStates.waiting_for_question)
async def unknown_in_state(message: Message):
    await message.answer(
        "📝 Отправьте текст вопроса или нажмите ❌ Отменить",
        reply_markup=cancel_keyboard
    )

@router.callback_query(F.data.startswith("approve_"))
async def approve_question(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    
    # Достаём текст вопроса из сообщения
    text = callback.message.text
    if "Текст: " in text:
        question_text = text.split("Текст: ", 1)[1]
    else:
        question_text = "Вопрос"
    
    try:
        # Отправляем в канал
        await bot.send_message(
            CHANNEL_ID,
            f"📨 <b>Анонимный вопрос:</b>\n\n{question_text}",
            parse_mode="HTML"
        )
        
        # Обновляем сообщение у админа
        await callback.message.edit_text(
            f"{callback.message.text}\n\n✅ Опубликовано в канале",
            parse_mode="HTML"
        )
        await callback.answer("✅ Опубликовано")
        
        # Уведомляем пользователя
        try:
            await bot.send_message(user_id, "✅ Ваш вопрос опубликован в канале!")
        except:
            pass
            
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)

@router.callback_query(F.data.startswith("reject_"))
async def reject_question(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    
    await callback.message.edit_text(
        f"{callback.message.text}\n\n❌ Отклонено",
        parse_mode="HTML"
    )
    await callback.answer("❌ Отклонено")
    
    try:
        await bot.send_message(
            user_id,
            "❌ Ваш вопрос отклонён администратором.\n\n"
            "Возможные причины: нарушение правил."
        )
    except:
        pass

# ========== ЗАПУСК ==========
async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    print("🚀 Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
