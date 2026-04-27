import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()  # Для Railway можно использовать MemoryStorage
    dp = Dispatcher(storage=storage)
    
    # Подключаем роутер
    dp.include_router(router)
    
    # Запуск бота
    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
