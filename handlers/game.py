from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import database
from config import ADMIN_IDS, SIMILARITY_THRESHOLD
from states import GameState, RegistrationState
from utils.matcher import calculate_similarity
from keyboards import (
    main_menu_keyboard,
    in_game_keyboard,
    after_answer_keyboard,
    contact_keyboard
)

router = Router()


def check_registered(user_id: int) -> bool:
    return database.is_user_registered(user_id)


@router.message(F.text.in_(["❓ Savol olish", "❓ Keyingi savol"]))
async def send_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if not check_registered(user_id):
        await state.set_state(RegistrationState.waiting_for_contact)
        await message.answer(
            "⚠️ O'yinni o'ynash uchun avval telefon raqamingizni yuboring:",
            reply_markup=contact_keyboard()
        )
        return

    # Tasodifiy savolni olish
    question = database.get_random_question(user_id)
    if not question:
        await message.answer(
            "😕 Hozircha bazada savollar mavjud emas.\n"
            "Tez orada yangi savollar qo'shiladi!",
            reply_markup=main_menu_keyboard(is_admin=user_id in ADMIN_IDS)
        )
        return

    # Holatni saqlash
    await state.update_data(
        question_id=question["id"],
        question_text=question["question"],
        correct_answer=question["answer"],
        explanation=question["explanation"] or ""
    )
    await state.set_state(GameState.waiting_for_answer)

    q_text = (
        f"🧠 <b>Zakovat savoli #{question['id']}</b>\n\n"
        f"❓ {question['question']}\n\n"
        f"<i>✍️ Javobingizni quyida yozib yuboring:</i>"
    )

    await message.answer(q_text, reply_markup=in_game_keyboard(), parse_mode="HTML")


@router.message(GameState.waiting_for_answer, F.text == "⏭ O'tkazib yuborish")
async def skip_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    q_id = data.get("question_id")
    correct_ans = data.get("correct_answer", "")
    explanation = data.get("explanation", "")

    if q_id:
        database.record_answer(
            user_id=user_id,
            question_id=q_id,
            user_answer="[O'tkazib yuborildi]",
            similarity=0.0,
            is_correct=False
        )

    await state.clear()

    resp = (
        f"⏭ <b>Savol o'tkazib yuborildi!</b>\n\n"
        f"💡 To'g'ri javob: <b>{correct_ans}</b>"
    )
    if explanation:
        resp += f"\nℹ️ <i>Izoh: {explanation}</i>"

    await message.answer(resp, reply_markup=after_answer_keyboard(), parse_mode="HTML")


@router.message(F.text == "🏠 Bosh menyu")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    await message.answer(
        "🏠 Asosiy menyudasiz. Qanday amal bajaramiz?",
        reply_markup=main_menu_keyboard(is_admin=is_admin)
    )


@router.message(GameState.waiting_for_answer, F.text)
async def process_user_answer(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_answer = message.text.strip()
    data = await state.get_data()

    q_id = data.get("question_id")
    correct_answer = data.get("correct_answer")
    explanation = data.get("explanation", "")

    if not q_id or not correct_answer:
        await state.clear()
        await message.answer(
            "Savol topilmadi yoki vaqti tugadi. Qaytadan '❓ Savol olish' tugmasini bosing.",
            reply_markup=main_menu_keyboard(is_admin=user_id in ADMIN_IDS)
        )
        return

    # O'xshashlikni hisoblash
    is_correct, similarity_pct, matched_variant = calculate_similarity(
        user_answer=user_answer,
        correct_answer=correct_answer,
        threshold=SIMILARITY_THRESHOLD
    )

    # Natijani bazaga yozish
    database.record_answer(
        user_id=user_id,
        question_id=q_id,
        user_answer=user_answer,
        similarity=similarity_pct,
        is_correct=is_correct
    )

    await state.clear()

    if is_correct:
        response_text = (
            f"🎉 <b>Ajoyib! To'g'ri javob! ✅</b>\n\n"
            f"💡 Javob: <b>{matched_variant}</b>\n"
        )
        if explanation:
            response_text += f"ℹ️ <i>Izoh: {explanation}</i>\n"
        response_text += "\n👏 Sizga <b>+1 ball</b> berildi!"
    else:
        response_text = (
            f"❌ <b>Afsuski, noto'g'ri javob!</b>\n\n"
            f"💡 To'g'ri javob: <b>{correct_answer}</b>\n"
        )
        if explanation:
            response_text += f"ℹ️ <i>Izoh: {explanation}</i>\n"
        response_text += "\nKeling, keyingi savolda omadingizni sinab ko'ring!"

    await message.answer(
        response_text,
        reply_markup=after_answer_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📊 Mening profilim")
async def show_profile(message: Message):
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    if not user:
        await message.answer("Siz hali ro'yxatdan o'tmagansiz. /start buyrug'ini bosing.")
        return

    name = user["first_name"]
    username = f"@{user['username']}" if user["username"] else "Mavjud emas"
    phone = user["phone_number"] or "Mavjud emas"
    score = user["score"]
    total = user["total_played"]
    
    accuracy = round((score / total) * 100, 1) if total > 0 else 0.0

    profile_text = (
        f"👤 <b>Foydalanuvchi profili:</b>\n\n"
        f"🏷 Ism: <b>{name}</b>\n"
        f"🔗 Nickname: <b>{username}</b>\n"
        f"📱 Telefon: <code>{phone}</code>\n"
        f"🏆 To'plangan ballar: <b>{score} ta</b>\n"
        f"🎮 Jami ishlangan savollar: <b>{total} ta</b>\n"
        f"🎯 Aniqlik (Samaradorlik): <b>{accuracy}%</b>\n"
    )
    
    await message.answer(profile_text, parse_mode="HTML")


@router.message(F.text == "🏆 Reyting")
async def show_leaderboard(message: Message):
    leaders = database.get_leaderboard(limit=10)
    
    if not leaders:
        await message.answer("Hozircha peshqadamlar ro'yxati bo'sh. Birinchi bo'lib ball to'plang!")
        return

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    text = "🏆 <b>Zakovat eng kuchli bilimdonlari (Top 10):</b>\n\n"
    for i, leader in enumerate(leaders):
        icon = medals[i] if i < len(medals) else f"{i+1}."
        leader_name = leader["first_name"]
        if leader["username"]:
            leader_name += f" (@{leader['username']})"
        score = leader["score"]
        total = leader["total_played"]
        text += f"{icon} <b>{leader_name}</b> — <b>{score} ball</b> ({total} ta urinish)\n"

    await message.answer(text, parse_mode="HTML")
