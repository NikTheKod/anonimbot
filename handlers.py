from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, CHANNEL_ID
from states import QuestionStates
from keyboards import main_keyboard, cancel_keyboard, admin_buttons

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🤖 <b>Анонимный бот вопросов</b>\n\n"
        "📌 <b>Правила:</b>\n"
        "• Запрещены оскорбления и мат\n"
        "• Запрещена реклама\n"
        "• Запрещена личная информация\n"
        "• Администратор проверяет каждый вопрос\n\n"
        "👇 <b>Нажмите кнопку ниже</b>",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )

@router.message(F.text == "📝 Задать анонимный вопрос")
async def ask_question(message: Message, state: FSMContext):
    await state.set_state(QuestionStates.waiting_for_question)
    await message.answer(
        "📝 <b>Напишите текст вопроса</b>\n\n"
        "❗️ Максимум 1000 символов\n"
        "❌ Для отмены нажмите кнопку\n\n"
        "<i>Вопрос будет отправлен на модерацию</i>",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )

@router.message(QuestionStates.waiting_for_question, F.text)
async def process_question(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer(
            "❌ Отправка вопроса отменена",
            reply_markup=main_keyboard
        )
        return
    
    if len(message.text) > 1000:
        await message.answer(
            "❌ Текст слишком длинный! Максимум 1000 символов.\nПопробуйте ещё раз:"
        )
        return
    
    question_text = message.text
    user_id = message.from_user.id
    
    admin_msg = await bot.send_message(
        ADMIN_ID,
        f"🆕 <b>НОВЫЙ АНОНИМНЫЙ ВОПРОС</b>\n\n"
        f"👤 ID отправителя: <code>{user_id}</code>\n"
        f"📝 <b>Текст вопроса:</b>\n"
        f"─────────────────────\n"
        f"{question_text}\n"
        f"─────────────────────\n\n"
        f"⬇️ <b>Выберите действие:</b>",
        reply_markup=admin_buttons(user_id),
        parse_mode="HTML"
    )
    
    await state.update_data(
        admin_msg_id=admin_msg.message_id,
        question_text=question_text,
        user_id=user_id
    )
    
    await message.answer(
        "✅ <b>Ваш вопрос отправлен на модерацию!</b>\n\n"
        "Администратор проверит его в ближайшее время.\n"
        "При соблюдении правил вопрос будет опубликован в канале.",
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )
    await state.clear()

@router.message(QuestionStates.waiting_for_question)
async def unknown_in_state(message: Message):
    await message.answer(
        "📝 Пожалуйста, отправьте <b>текст</b> вашего вопроса\n"
        "Или нажмите ❌ Отменить",
        reply_markup=cancel_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("approve_"))
async def approve_question(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    
    text = callback.message.text
    
    # Извлекаем текст вопроса
    if "─────────────────────\n" in text:
        parts = text.split("─────────────────────\n")
        if len(parts) >= 2:
            question_text = parts[1].split("\n─────────────────────")[0]
        else:
            question_text = "Текст вопроса не найден"
    else:
        question_text = "Текст вопроса не найден"
    
    try:
        await bot.send_message(
            CHANNEL_ID,
            f"📨 <b>Анонимный вопрос:</b>\n\n{question_text}",
            parse_mode="HTML"
        )
        
        await callback.message.edit_text(
            f"{callback.message.text}\n\n✅ <b>Вопрос опубликован в канале</b>",
            parse_mode="HTML"
        )
        await callback.answer("✅ Вопрос опубликован", show_alert=False)
        
        try:
            await bot.send_message(
                user_id,
                "✅ <b>Ваш вопрос опубликован в канале!</b>\n\n"
                "Спасибо за участие 🙌",
                parse_mode="HTML"
            )
        except Exception:
            pass
            
    except Exception as e:
        await callback.answer(f"Ошибка при публикации: {e}", show_alert=True)

@router.callback_query(F.data.startswith("reject_"))
async def reject_question(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[1])
    
    await callback.message.edit_text(
        f"{callback.message.text}\n\n❌ <b>Вопрос отклонён модератором</b>",
        parse_mode="HTML"
    )
    await callback.answer("❌ Вопрос отклонён", show_alert=False)
    
    try:
        await bot.send_message(
            user_id,
            "❌ <b>Ваш вопрос был отклонён администратором</b>\n\n"
            "Возможные причины отклонения:\n"
            "• Нарушение правил сообщества\n"
            "• Некорректное или оскорбительное содержание\n"
            "• Спам или реклама\n\n"
            "Вы можете задать другой вопрос, соблюдая правила.",
            parse_mode="HTML"
        )
    except Exception:
        pass
