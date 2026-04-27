from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Главная клавиатура (Reply-кнопки)
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📝 Задать анонимный вопрос")]],
    resize_keyboard=True
)

# Клавиатура для отмены
cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отменить")]],
    resize_keyboard=True
)

# Клавиатура для админа (на каждый вопрос)
def admin_buttons(user_id: int, question_text: str):
    # Ограничиваем длину callback_data (макс 64 байта)
    # Поэтому храним только user_id, а текст вопроса будем доставать из сообщения
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить в канал",
                    callback_data=f"approve_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_{user_id}"
                )
            ]
        ]
    )
