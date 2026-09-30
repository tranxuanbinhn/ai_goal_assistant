import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from src.core.db.database import init_db
from src.integrations.bot_handlers import router
from dotenv import load_dotenv
load_dotenv()
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Nạp toàn bộ router xử lý giao diện
    dp.include_router(router)
    
    print("Bot đang chạy...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())