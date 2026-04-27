import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID
from handlers import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Проверяем переменные ТОЛЬКО при запуске
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN не найден в переменных окружения")
        sys.exit(1)
    
    if not ADMIN_ID:
        logging.error("❌ ADMIN_ID не найден в переменных окружения")
        sys.exit(1)
    
    if not CHANNEL_ID:
        logging.error("❌ CHANNEL_ID не найден в переменных окружения")
        sys.exit(1)
    
    # Конвертируем ADMIN_ID в int
    try:
        ADMIN_ID_INT = int(ADMIN_ID)
    except ValueError:
        logging.error(f"❌ ADMIN_ID должен быть числом, получено: {ADMIN_ID}")
        sys.exit(1)
    
    logging.info(f"✅ Переменные загружены:")
    logging.info(f"   ADMIN_ID: {ADMIN_ID_INT}")
    logging.info(f"   CHANNEL_ID: {CHANNEL_ID}")
    
    # Сохраняем в handlers (через глобальную переменную или импорт)
    import handlers
    handlers.ADMIN_ID = ADMIN_ID_INT
    
    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(router)
    
    logging.info("🚀 Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
