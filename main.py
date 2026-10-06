import asyncio
import logging
import sys

# Windows konsolida emojilar va belgilar to'g'ri chiqishi uchun UTF-8 ga o'tkazish
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database
from handlers import start_router, game_router, admin_router

# Loggingni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def main():
    # 1. Ma'lumotlar bazasini initsializatsiya qilish
    logger.info("Ma'lumotlar bazasi ishga tushirilmoqda...")
    database.init_db()

    # 2. Token tekshiruvi
    if not BOT_TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in BOT_TOKEN:
        logger.error(
            "\n" + "=" * 60 + "\n"
            "❌ XATOLIK: BOT_TOKEN ko'rsatilmagan!\n"
            "Iltimos, '.env' faylini oching va Telegram @BotFather dan olingan bot tokeningizni kiriting:\n"
            "BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11\n"
            "=" * 60
        )
        return

    # 3. Bot va Dispatcher obyektlarini yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Routerlarni ulash
    # Tartib muhim: start -> game -> admin
    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(game_router)

    # 5. Botni ishga tushirish
    try:
        bot_info = await bot.get_me()
        logger.info(f"🤖 Bot muvaffaqiyatli ishga tushdi: @{bot_info.username}")
        print("\n" + "=" * 50)
        print(f"🚀 Zakovat Bot ishga tushdi: @{bot_info.username}")
        print("Bot xabarlarni qabul qilishga tayyor...")
        print("=" * 50 + "\n")
        
        # Eski o'qilmagan xabarlarni tashlab yuborish
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik yuz berdi: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi!")
