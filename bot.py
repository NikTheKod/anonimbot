import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID, CHANNEL_ID
from handlers import router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    # Проверка переменных окружения
    if not BOT_TOKEN:
        logging.error("❌ Ошибка: BOT_TOKEN не найден в переменных окружения")
        sys.exit(1)
    
    if not ADMIN_ID:
        logging.error("❌ Ошибка: ADMIN_ID не найден в переменных окружения")
        sys.exit(1)
    
    if not CHANNEL_ID:
        logging.error("❌ Ошибка: CHANNEL_ID не найден в переменных окружения")
        sys.exit(1)
    
    # Конвертируем ADMIN_ID в int (если строка)
    try:
        import handlers
        handlers.ADMIN_ID = int(ADMIN_ID)
    except ValueError:
        logging.error(f"❌ ADMIN_ID должен быть числом, получено: {ADMIN_ID}")
        sys.exit(1)
    
    # Проверка CHANNEL_ID (может быть строкой с @ или числом)
    if str(CHANNEL_ID).lstrip('-').isdigit():
        logging.info(f"✅ CHANNEL_ID: {CHANNEL_ID} (числовой формат)")
    else:
        logging.info(f"✅ CHANNEL_ID: {CHANNEL_ID} (username формат)")
    
    logging.info("🤖 Запуск анонимного бота...")
    
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(router)
    
    logging.info("✅ Бот успешно запущен и готов к работе")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logging.info("⏹ Бот остановлен")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
