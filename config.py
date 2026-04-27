import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Твой Telegram ID
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Например: @channel или -1001234567890

# Проверка наличия переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не найден в .env")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID не найден в .env")
