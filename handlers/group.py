import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

import database
from config import ADMIN_IDS, SIMILARITY_THRESHOLD
from utils.matcher import calculate_similarity
from keyboards import next_question_inline

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

    # Guruh holatini faollashtirish
    database.set_group_auto_status(chat_id, True, title=message.chat.title or "Guruh")
    
    # Guruhda faol savol bormi tekshirish
    group = database.get_group(chat_id)
    if group and group["current_question_id"]:
        await message.answer("⚠️ Guruhda allaqachon faol savol mavjud! Avval unga javob bering.")
        return

    question = database.get_random_question()
    if not question:
        await message.answer("Bazada hozircha savollar yo'q.")
        return

    q_text = (
        f"🚀 <b>Guruhda Zakovat o'yini boshlandi!</b>\n\n"
        f"🧠 <b>Zakovat savoli #{question['id']}</b>\n\n"
        f"❓ {question['question']}\n\n"
        f"⏳ <i>Javob berish uchun 90 soniya vaqtingiz bor!</i>\n"
        f"🎯 <i>To'g'ri javob uchun: <b>+10 ball</b></i>"
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
        "🛑 <b>Zakovat o'yini to'xtatildi.</b>\n\n"
        "Qayta boshlash uchun: /start_quiz",
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
        f"⏳ <i>Javob berish uchun 90 soniya vaqtingiz bor!</i>\n"
        f"🎯 <i>To'g'ri javob uchun: <b>+10 ball</b></i>"
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


@router.callback_query(F.data == "group_next_q")
async def callback_group_next_question(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    group = database.get_group(chat_id)
    
    # Guruhda hozir faol savol bormi tekshirish
    if group and group["current_question_id"]:
        await callback.answer("⚠️ Hozirda faol savol mavjud! Avval unga javob bering.", show_alert=True)
        return
        
    question = database.get_random_question()
    if not question:
        await callback.answer("Bazada savollar tugadi.", show_alert=True)
        return
        
    await callback.answer("Yangi savol!")
    
    q_text = (
        f"🧠 <b>Zakovat savoli #{question['id']}</b>\n\n"
        f"❓ {question['question']}\n\n"
        f"⏳ <i>Javob berish uchun 90 soniya vaqtingiz bor!</i>\n"
        f"🎯 <i>To'g'ri javob uchun: <b>+10 ball</b></i>"
    )

    image_id = question["image_id"] if "image_id" in question.keys() else None
    if image_id:
        await callback.message.answer_photo(photo=image_id, caption=q_text, parse_mode="HTML")
    else:
        await callback.message.answer(q_text, parse_mode="HTML")

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

        # Guruhdagi foydalanuvchi hisobiga +10 ball qo'shish
        new_score = database.add_group_user_score(
            chat_id=chat_id,
            user_id=user.id,
            first_name=first_name,
            username=username
        )

        explanation = group["current_explanation"]
        
        # Faol savolni tozalash (keyingi savolga tayyorlash)
        database.clear_group_current_question(chat_id)

        resp = (
            f"🎉 <b>To'g'ri javob!</b>\n\n"
            f"👏 G'olib: {mention}\n"
            f"💡 Javob: <b>{matched_variant}</b>\n"
        )
        if explanation:
            resp += f"ℹ️ <i>Izoh: {explanation}</i>\n"
            
        resp += (
            f"\n🏆 Guruhdagi to'plangan ball: <b>{new_score} ta</b> (<b>+10 ball</b>)\n\n"
            f"👇 <i>Keyingi savolga tayyor bo'lsangiz, pastdagi tugmani bosing:</i>"
        )
        await message.reply(resp, reply_markup=next_question_inline(), parse_mode="HTML")
