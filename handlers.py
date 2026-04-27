import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from config import ADMIN_ID, CHANNEL_ID
from states import QuestionStates
from keyboards import main_keyboard, cancel_keyboard, admin_buttons

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
        "• После отправки вопроса дождитесь модерации\n"
        "• Если ваш вопрос отклонят, вы получите уведомление\n\n"
        "👇 <b>Нажмите кнопку ниже, чтобы задать вопрос</b>",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )

# Кнопка "Задать анонимный вопрос"
@router.message(F.text == "📝 Задать анонимный вопрос")
async def ask_question(message: Message, state: FSMContext):
    await state.set_state(QuestionStates.waiting_for_question)
    await message.answer(
        "📝 <b>Напишите текст вашего вопроса</b>\n\n"
        "❗️ <b>Правила:</b>\n"
        "• Не используйте мат и оскорбления\n"
        "• Не публикуйте личную информацию\n"
        "• Не рекламируйте что-либо\n\n"
        "⏸ <i>Для отмены нажмите кнопку \"Отменить\"</i>",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )

# Обработка текста вопроса
@router.message(QuestionStates.waiting_for_question, F.text)
async def process_question(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Отправка вопроса отменена",
            reply_markup=main_keyboard
        )
        return
    
    question_text = message.text
    user_id = message.from_user.id
    
    # Отправляем админу на модерацию
    admin_message = await bot.send_message(
        ADMIN_ID,
        f"🆕 <b>Новый анонимный вопрос</b>\n\n"
        f"👤 <b>От пользователя:</b> <code>{user_id}</code>\n"
        f"📝 <b>Текст:</b>\n{question_text}\n\n"
        f"⬇️ <b>Примите решение:</b>",
        reply_markup=admin_buttons(user_id, question_text),
        parse_mode="HTML"
    )
    
    # Сохраняем в FSM ID сообщения админа и текст вопроса
    await state.update_data(
        admin_msg_id=admin_message.message_id,
        question_text=question_text,
        user_id=user_id
    )
    
    await message.answer(
        "✅ Ваш вопрос отправлен на модерацию!\n"
        "Администратор проверит его и опубликует, если он соответствует правилам.",
        reply_markup=main_keyboard
    )
    await state.clear()

# Обработка неизвестного текста в состоянии ожидания
@router.message(QuestionStates.waiting_for_question)
async def process_unknown(message: Message):
    await message.answer(
        "📝 Пожалуйста, отправьте текст вопроса или нажмите ❌ Отменить",
        reply_markup=cancel_keyboard
    )

# Кнопка "Отправить" у админа
@router.callback_query(F.data.startswith("approve_"))
async def approve_question(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    
    # Достаем текст вопроса из оригинального сообщения админа
    # Сообщение админа: callback.message
    parts = callback.message.text.split("\n\n")
    if len(parts) >= 3:
        # Ищем строку с "Текст:" и берем всё после неё
        for i, part in enumerate(parts):
            if part.startswith("📝 <b>Текст:</b>"):
                question_text = part.replace("📝 <b>Текст:</b>\n", "")
                break
        else:
            # fallback
            question_text = "Текст вопроса не найден"
    else:
        question_text = "Текст вопроса не найден"
    
    # Публикуем в канал
    try:
        await bot.send_message(
            CHANNEL_ID,
            f"📨 <b>Анонимный вопрос:</b>\n\n{question_text}",
            parse_mode="HTML"
        )
        
        # Уведомляем админа
        await callback.message.edit_text(
            f"{callback.message.text}\n\n✅ <b>Вопрос опубликован в канале</b>",
            parse_mode="HTML"
        )
        await callback.answer("✅ Вопрос опубликован")
        
        # Сообщаем пользователю об успехе
        try:
            await bot.send_message(
                user_id,
                "✅ <b>Ваш вопрос был опубликован в канале!</b>\n\n"
                "Спасибо за участие 🙌",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")
            
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)

# Кнопка "Отклонить" у админа
@router.callback_query(F.data.startswith("reject_"))
async def reject_question(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    
    # Уведомляем админа
    await callback.message.edit_text(
        f"{callback.message.text}\n\n❌ <b>Вопрос отклонен</b>",
        parse_mode="HTML"
    )
    await callback.answer("❌ Вопрос отклонен")
    
    # Отправляем уведомление пользователю
    try:
        await bot.send_message(
            user_id,
            "❌ <b>Ваш вопрос был отклонён администратором.</b>\n\n"
            "Возможные причины:\n"
            "• Нарушение правил чата\n"
            "• Некорректное содержание\n"
            "• Спам или реклама\n\n"
            "Вы можете задать другой вопрос, соблюдая правила.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Не удалось отправить отказ пользователю {user_id}: {e}")
