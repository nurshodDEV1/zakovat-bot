import os
from dotenv import load_dotenv

# .env faylidan o'zgaruvchilarni yuklash
load_dotenv()

# Telegram Bot Token (BotFather'dan olinadi)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Adminlarning Telegram ID raqamlari (vergul bilan ajratilgan bo'lishi mumkin)
admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [
    int(x.strip()) 
    for x in admin_ids_raw.split(",") 
    if x.strip().isdigit()
]

# Javobni to'g'ri deb hisoblash uchun minimal o'xshashlik foizi (talabga ko'ra 90%)
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 90.0))
