import asyncio
import time
import logging
from aiogram import Bot

import database
from keyboards import next_question_inline

logger = logging.getLogger(__name__)

async def run_group_auto_quiz(bot: Bot):
    """
    Guruhlardagi faol savollar vaqtini (90 soniya) kuzatib boruvchi xizmat.
    Agar vaqt tugasa, to'g'ri javobni chiqaradi va '❓ Keyingi savol' tugmasini qoldiradi.
    Avtomatik tarzda savol yubormaydi — savol faqat foydalanuvchi tugmani bosganda yuboriladi!
    """
    logger.info("Guruhlar uchun savollar vaqtini nazorat qilish xizmati ishga tushdi...")
    
    while True:
        try:
            active_groups = database.get_active_groups()
            now = time.time()
            
            for group in active_groups:
                chat_id = group["chat_id"]
                current_q_id = group["current_question_id"]
                sent_at = group["question_sent_at"] or 0
                timeout = group["timeout_seconds"] or 90
                
                # Agar savol berilgan bo'lsa va vaqti tugagan bo'lsa
                if current_q_id and (now - sent_at >= timeout):
                    correct_ans = group["current_answer"]
                    explanation = group["current_explanation"]
                    
                    resp = (
                        f"⏰ <b>Vaqt tugadi!</b>\n"
                        f"Hech kim to'g'ri javob bera olmadi.\n\n"
                        f"💡 To'g'ri javob: <b>{correct_ans}</b>"
                    )
                    if explanation:
                        resp += f"\nℹ️ <i>Izoh: {explanation}</i>"
                    
                    resp += "\n\n👇 <i>Keyingi savolni olish uchun pastdagi tugmani bosing:</i>"
                    
                    try:
                        await bot.send_message(
                            chat_id=chat_id, 
                            text=resp, 
                            reply_markup=next_question_inline(),
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.warning(f"Guruhga vaqt tugash xabarini yuborishda xatolik ({chat_id}): {e}")
                        
                    database.clear_group_current_question(chat_id)

        except Exception as e:
            logger.error(f"Group quiz monitoring siklida xatolik: {e}")

        # Har 5 soniyada tekshirish
        await asyncio.sleep(5)
