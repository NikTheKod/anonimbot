import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from states import QuestionStates
from keyboards import main_keyboard, cancel_keyboard, admin_buttons

# Эти переменные будут установлены из bot.py
ADMIN_ID = None
CHANNEL_ID = None

# Импортируем config для получения CHANNEL_ID (но не ADMIN_ID)
from config import CHANNEL_ID as CONFIG_CHANNEL_ID
CHANNEL_ID = CONFIG_CHANNEL_ID

router = Router()

# Команда /start
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 <b>Добро пожаловать в анонимный бот!</b>\n\n"
        "📌 <b>Правила:</b>\n"
        "• Вопросы должны быть корректными и без оскорблений\n"
        "• Администратор проверяет каждый вопрос перед публикацией\n"
        "• После отправки вопроса дождитесь модерации\n\n"
        "👇 <b>Нажмите кнопку ниже, чтобы задать вопрос</b>",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )

# Остальные хендлеры такие же, но используем ADMIN_ID из глобальной переменной
# В функциях approve_question и reject_question нужно заменить 
# ADMIN_ID на глобальную переменную из этого модуля
