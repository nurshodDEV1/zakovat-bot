import time
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.filters import Command

import database
from config import ADMIN_IDS, SIMILARITY_THRESHOLD
from utils.matcher import calculate_similarity

router = Router()

async def is_admin_or_group_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Foydalanuvchi bot admini yoki guruh admini ekanligini tekshiradi"""
    if user_id in ADMIN_IDS:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ["creator", "administrator"]
    except Exception:
        return False


# ================= GURUH BUYRUQLARI =================

@router.message(F.chat.type.in_(["group", "supergroup"]), Command("start_quiz", "boshlash"))
async def cmd_start_quiz(message: Message, bot: Bot):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not await is_admin_or_group_admin(bot, chat_id, user_id):
        await message.reply("⛔️ Bu buyruqdan faqat guruh adminlari foydalana oladi!")
        return

    # Guruhda avto-savolni yoqish
    database.set_group_auto_status(chat_id, True, title=message.chat.title or "Guruh")
    
    # Birinchi savol darhol (bir necha soniya ichida) chiqishi uchun last_action_at ni orqaga suramiz
    with database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE groups SET last_action_at = ? WHERE chat_id = ?",
            (time.time() - 175, chat_id)
        )
        conn.commit()

    group = database.get_group(chat_id)
    interval_min = max(1, round((group["interval_seconds"] or 180) / 60))

    text = (
        "🚀 <b>Zakovat avto-savol rejimi YOQILDI!</b>\n\n"
        f"⏱ Savollar oralig'i: <b>{interval_min} daqiqa</b>\n"
        "⏳ Javob berish vaqti: <b>90 soniya</b>\n\n"
        "📌 <i>Birinchi savol bir necha soniya ichida yuboriladi. Barchaga omad!</i>\n\n"
        "🛠 <b>Boshqaruv buyruqlari:</b>\n"
        "• /stop_quiz — O'yinni to'xtatish\n"
        "• /interval [daqiqa] — Oraliq vaqtini o'zgartirish (masalan: <code>/interval 2</code>)\n"
        "• /savol — Navbatdan tashqari savol olish\n"
        "• /reyting — Guruh peshqadamlari ro'yxati"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.chat.type.in_(["group", "supergroup"]), Command("stop_quiz", "toxtatish"))
async def cmd_stop_quiz(message: Message, bot: Bot):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not await is_admin_or_group_admin(bot, chat_id, user_id):
        await message.reply("⛔️ Bu buyruqdan faqat guruh adminlari foydalana oladi!")
        return

    database.set_group_auto_status(chat_id, False)
    database.clear_group_current_question(chat_id)

    await message.answer(
        "🛑 <b>Zakovat avto-savol rejimi to'xtatildi.</b>\n\n"
        "Qayta yoqish uchun: /start_quiz",
        parse_mode="HTML"
    )


@router.message(F.chat.type.in_(["group", "supergroup"]), Command("interval"))
async def cmd_change_interval(message: Message, bot: Bot):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if not await is_admin_or_group_admin(bot, chat_id, user_id):
        await message.reply("⛔️ Bu buyruqdan faqat guruh adminlari foydalana oladi!")
        return

    parts = message.text.strip().split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply(
            "Iltimos, oraliq vaqtini daqiqada kiriting.\n"
            "Masalan: <code>/interval 3</code> (har 3 daqiqada yangi savol)",
            parse_mode="HTML"
        )
        return

    minutes = int(parts[1])
    if minutes < 1 or minutes > 60:
        await message.reply("Interval 1 dan 60 daqiqagacha bo'lishi mumkin.")
        return

    database.set_group_interval(chat_id, minutes)
    await message.answer(
        f"⏱ <b>Savollar oralig'i {minutes} daqiqaga o'zgartirildi!</b>",
        parse_mode="HTML"
    )


@router.message(F.chat.type.in_(["group", "supergroup"]), Command("savol"))
async def cmd_manual_question(message: Message):
    chat_id = message.chat.id
    group = database.get_group(chat_id)
    
    if group and group["current_question_id"]:
        await message.reply(
            "⚠️ Hozirda faol savol mavjud! Avval unga javob bering yoki vaqti tugashini kuting."
        )
        return

    question = database.get_random_question()
    if not question:
        await message.answer("Bazada hozircha savollar yo'q.")
        return

    q_text = (
        f"🧠 <b>Zakovat savoli #{question['id']}</b>\n\n"
        f"❓ {question['question']}\n\n"
        f"⏳ <i>Javob berish uchun 90 soniya vaqtingiz bor!</i>"
    )

    image_id = question["image_id"] if "image_id" in question.keys() else None
    if image_id:
        await message.answer_photo(photo=image_id, caption=q_text, parse_mode="HTML")
    else:
        await message.answer(q_text, parse_mode="HTML")

    database.set_group_current_question(
        chat_id=chat_id,
        question_id=question["id"],
        answer=question["answer"],
        explanation=question["explanation"] or "",
        image_id=image_id
    )


@router.message(F.chat.type.in_(["group", "supergroup"]), Command("reyting", "top"))
async def cmd_group_leaderboard(message: Message):
    chat_id = message.chat.id
    leaders = database.get_group_leaderboard(chat_id, limit=10)
    
    if not leaders:
        await message.answer("Ushbu guruhda hozircha hech kim ball to'plamagan.")
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    text = "🏆 <b>Ushbu guruh bilimdonlari reytingi (Top 10):</b>\n\n"
    
    for i, leader in enumerate(leaders):
        icon = medals[i] if i < len(medals) else f"{i+1}."
        name = leader["first_name"]
        if leader["username"]:
            name += f" (@{leader['username']})"
        score = leader["score"]
        text += f"{icon} <b>{name}</b> — <b>{score} ball</b>\n"

    await message.answer(text, parse_mode="HTML")


# ================= GURUHDAGI JAVOBLARNI TEKSHIRISH =================

@router.message(F.chat.type.in_(["group", "supergroup"]), F.text)
async def handle_group_answer(message: Message):
    # Agar buyruq bo'lsa, tekshirmaymiz
    if message.text.startswith("/"):
        return

    chat_id = message.chat.id
    group = database.get_group(chat_id)
    
    # Guruhda hozir faol savol bormi?
    if not group or not group["current_answer"]:
        return

    correct_answer = group["current_answer"]
    user_answer = message.text.strip()
    
    # 90% o'xshashlik tekshiruvi
    is_correct, similarity_pct, matched_variant = calculate_similarity(
        user_answer=user_answer,
        correct_answer=correct_answer,
        threshold=SIMILARITY_THRESHOLD
    )

    if is_correct:
        user = message.from_user
        first_name = user.first_name or "Foydalanuvchi"
        username = user.username
        mention = f"@{username}" if username else f"<b>{first_name}</b>"

        # Guruhdagi foydalanuvchi hisobiga ball qo'shish
        new_score = database.add_group_user_score(
            chat_id=chat_id,
            user_id=user.id,
            first_name=first_name,
            username=username
        )

        explanation = group["current_explanation"]
        
        # Faol savolni tozalash (keyingi savolga tayyorlash)
        database.clear_group_current_question(chat_id)

        interval_min = max(1, round((group["interval_seconds"] or 180) / 60))

        resp = (
            f"🎉 <b>To'g'ri javob!</b>\n\n"
            f"👏 G'olib: {mention}\n"
            f"💡 Javob: <b>{matched_variant}</b>\n"
        )
        if explanation:
            resp += f"ℹ️ <i>Izoh: {explanation}</i>\n"
            
        resp += (
            f"\n🏆 Guruhdagi to'plangan ball: <b>{new_score} ta</b> (+1 ball)\n"
            f"⏱ Keyingi savol <b>{interval_min} daqiqa</b>dan so'ng yuboriladi..."
        )
        await message.reply(resp, parse_mode="HTML")
