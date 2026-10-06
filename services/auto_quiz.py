import asyncio
import time
import logging
from aiogram import Bot

import database

logger = logging.getLogger(__name__)

async def run_group_auto_quiz(bot: Bot):
    """
    Guruhlarda avtomatik savol berish sikli.
    Fon rejimida tinimsiz ishlaydi va faol guruhlarni tekshiradi:
    1. Agar savolga belgilangan vaqt (90 soniya) ichida javob berilmasa, vaqt tugagani va to'g'ri javob e'lon qilinadi.
    2. Savollar orasidagi interval (masalan 3 daqiqa) o'tgach, yangi tasodifiy savol yuboriladi.
    """
    logger.info("Guruhlar uchun avto-savol xizmati ishga tushdi...")
    
    while True:
        try:
            active_groups = database.get_active_groups()
            now = time.time()
            
            for group in active_groups:
                chat_id = group["chat_id"]
                current_q_id = group["current_question_id"]
                sent_at = group["question_sent_at"] or 0
                last_action = group["last_action_at"] or 0
                interval = group["interval_seconds"] or 180
                timeout = group["timeout_seconds"] or 90
                
                # 1. Joriy savol vaqti tugaganmi tekshirish
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
                    
                    interval_min = max(1, round(interval / 60))
                    resp += f"\n\n⏱ Keyingi savol <b>{interval_min} daqiqa</b>dan so'ng yuboriladi..."
                    
                    try:
                        await bot.send_message(chat_id=chat_id, text=resp, parse_mode="HTML")
                    except Exception as e:
                        logger.warning(f"Guruhga xabar yuborishda xatolik ({chat_id}): {e}")
                        
                    database.clear_group_current_question(chat_id)
                    continue

                # 2. Yangi savol yuborish vaqti keldimi tekshirish
                if not current_q_id and (now - last_action >= interval):
                    question = database.get_random_question()
                    if not question:
                        # Savollar yo'q bo'lsa
                        continue
                    
                    q_text = (
                        f"🧠 <b>Zakovat savoli #{question['id']}</b>\n\n"
                        f"❓ {question['question']}\n\n"
                        f"⏳ <i>Javob berish uchun {timeout} soniya vaqtingiz bor!</i>"
                    )
                    
                    image_id = question["image_id"] if "image_id" in question.keys() else None
                    
                    try:
                        if image_id:
                            await bot.send_photo(
                                chat_id=chat_id,
                                photo=image_id,
                                caption=q_text,
                                parse_mode="HTML"
                            )
                        else:
                            await bot.send_message(
                                chat_id=chat_id,
                                text=q_text,
                                parse_mode="HTML"
                            )
                            
                        database.set_group_current_question(
                            chat_id=chat_id,
                            question_id=question["id"],
                            answer=question["answer"],
                            explanation=question["explanation"] or "",
                            image_id=image_id
                        )
                    except Exception as e:
                        logger.warning(f"Savol yuborishda xatolik ({chat_id}): {e}")
                        database.clear_group_current_question(chat_id)

        except Exception as e:
            logger.error(f"Auto-quiz siklida xatolik: {e}")

        # Har 5 soniyada tekshirish
        await asyncio.sleep(5)
