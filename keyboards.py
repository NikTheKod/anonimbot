from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Главное меню (Reply кнопки)
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Отправить анонимное сообщение")],
        [KeyboardButton(text="📜 Правила"), KeyboardButton(text="ℹ️ О нас")]
    ],
    resize_keyboard=True
)

# Кнопка отмены во время написания сообщения
cancel_button = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отменить отправку")]
    ],
    resize_keyboard=True
)

# Кнопки для админа (одобрить/отклонить)
def get_admin_keyboard(bot_message_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Опубликовать в канал", callback_data=f"approve_{bot_message_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{bot_message_id}")
            ]
        ]
    )

# Кнопка удалить своё сообщение (для пользователя после отправки)
def get_delete_keyboard(bot_message_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Удалить обращение", callback_data=f"delete_{bot_message_id}")]
        ]
    )
