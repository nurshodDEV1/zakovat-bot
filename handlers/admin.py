from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

import database
from config import ADMIN_IDS
from states import AdminState
from keyboards import (
    admin_menu_keyboard,
    cancel_keyboard,
    main_menu_keyboard,
    question_delete_inline
)

router = Router()

def is_admin(user_id: int) -> bool:
    # Agar ADMIN_IDS bo'sh bo'lsa, xavfsizlik uchun hech kimni admin qilmaymiz
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
@router.message(F.text == "⚙️ Admin panel")
async def open_admin_panel(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("⛔️ Kechirasiz, sizda admin huquqi yo'q!")
        return
        
    await message.answer(
        "🛠 <b>Admin boshqaruv paneliga xush kelibsiz!</b>\n\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_admin_action(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if is_admin(user_id):
        await message.answer(
            "Amal bekor qilindi.",
            reply_markup=admin_menu_keyboard()
        )
    else:
        await message.answer(
            "Amal bekor qilindi.",
            reply_markup=main_menu_keyboard()
        )


@router.message(F.text == "📊 Statistika")
async def admin_statistics(message: Message):
    if not is_admin(message.from_user.id):
        return

    stats = database.get_statistics()
    text = (
        "📊 <b>Botning umumiy statistikasi:</b>\n\n"
        f"👥 Jami ro'yxatdan o'tgan foydalanuvchilar: <b>{stats['total_users']} ta</b>\n"
        f"❓ Bazadagi jami savollar: <b>{stats['total_questions']} ta</b>\n"
        f"📝 Berilgan jami javoblar: <b>{stats['total_answers']} ta</b>\n"
        f"✅ To'g'ri topilgan javoblar: <b>{stats['correct_answers']} ta</b>\n"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🗑 Barcha savollarni tozalash")
async def handle_clear_all_questions(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    database.clear_all_questions()
    await message.answer(
        "🗑 <b>Barcha savollar va javoblar tarixi muvaffaqiyatli o'chirildi!</b>\n"
        "Hozirda bazada 0 ta savol mavjud. Yangi savollarni '➕ Yangi savol qo'shish' tugmasi orqali kiritishingiz mumkin.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "➕ Yangi savol qo'shish")
async def start_add_question(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
        
    await state.set_state(AdminState.waiting_for_question_text)
    await message.answer(
        "📝 <b>Yangi savol matnini kiriting:</b>\n\n"
        "<i>Bekor qilish uchun pastdagi tugmani bosing.</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminState.waiting_for_question_text, F.text)
async def process_question_text(message: Message, state: FSMContext):
    await state.update_data(question_text=message.text.strip())
    await state.set_state(AdminState.waiting_for_answer_text)
    
    await message.answer(
        "💡 <b>Endi ushbu savolning to'g'ri javobini kiriting:</b>\n\n"
        "<i>Eslatma: Agar bir nechta to'g'ri variant bo'lsa, ularni <b>|</b> belgisi bilan ajratishingiz mumkin.\n"
        "Masalan: <code>Amir Temur | Temurbek | Sohibqiron</code></i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminState.waiting_for_answer_text, F.text)
async def process_answer_text(message: Message, state: FSMContext):
    await state.update_data(answer_text=message.text.strip())
    await state.set_state(AdminState.waiting_for_explanation)
    
    skip_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏩ Izohni o'tkazib yuborish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "ℹ️ <b>Savol uchun izoh (tushuntirish) kiritasizmi?</b>\n\n"
        "Agar izoh kerak bo'lmasa, '⏩ Izohni o'tkazib yuborish' tugmasini bosing:",
        reply_markup=skip_kb,
        parse_mode="HTML"
    )


@router.message(AdminState.waiting_for_explanation, F.text)
async def process_explanation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    explanation = ""
    if message.text != "⏩ Izohni o'tkazib yuborish":
        explanation = message.text.strip()
        
    data = await state.get_data()
    q_text = data.get("question_text")
    a_text = data.get("answer_text")
    
    new_id = database.add_question(
        question=q_text,
        answer=a_text,
        explanation=explanation
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Savol muvaffaqiyatli saqlandi!</b>\n\n"
        f"🆔 ID: #{new_id}\n"
        f"❓ Savol: {q_text}\n"
        f"💡 Javob: {a_text}\n"
        f"ℹ️ Izoh: {explanation or 'Mavjud emas'}",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Savollar ro'yxati")
async def list_questions(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    questions = database.get_all_questions()
    if not questions:
        await message.answer("Bazada hozircha savollar yo'q.")
        return

    # Savollarning oxirgi 10 tasini ko'rsatish
    display_questions = questions[:10]
    total = len(questions)
    
    await message.answer(f"📋 <b>Bazada jami {total} ta savol bor. Oxirgi savollar:</b>", parse_mode="HTML")
    
    for q in display_questions:
        q_info = (
            f"🆔 <b>Savol #{q['id']}</b>\n"
            f"❓ {q['question']}\n"
            f"💡 Javob: <code>{q['answer']}</code>\n"
        )
        if q['explanation']:
            q_info += f"ℹ️ Izoh: <i>{q['explanation']}</i>\n"
            
        await message.answer(
            q_info,
            reply_markup=question_delete_inline(q['id']),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("del_q:"))
async def delete_question_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Siz admin emassiz!", show_alert=True)
        return
        
    q_id = int(callback.data.split(":")[1])
    success = database.delete_question(q_id)
    
    if success:
        await callback.answer("Savol o'chirildi! 🗑")
        await callback.message.edit_text(f"❌ <b>#{q_id} raqamli savol o'chirildi!</b>", parse_mode="HTML")
    else:
        await callback.answer("Savol topilmadi yoki allaqachon o'chirilgan.", show_alert=True)
