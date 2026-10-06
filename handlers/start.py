from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database
from config import ADMIN_IDS
from states import RegistrationState
from keyboards import contact_keyboard, main_menu_keyboard, add_to_group_inline

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    user_id = user.id
    name = user.first_name or "Foydalanuvchi"
    is_admin = user_id in ADMIN_IDS

    # Agar admin bo'lsa va hali bazada bo'lmasa, uni avtomatik ro'yxatdan o'tkazamiz
    if is_admin and not database.is_user_registered(user_id):
        database.save_user(user_id=user_id, first_name=name, username=user.username, phone_number="Admin")

    # Foydalanuvchi bazada telefon raqami bilan bormi?
    if database.is_user_registered(user_id):
        bot_info = await message.bot.get_me()
        bot_username = bot_info.username or "zakovatgazganbot"
        await message.answer(
            "🏠 <b>Asosiy menyu:</b>",
            reply_markup=main_menu_keyboard(is_admin=is_admin),
            parse_mode="HTML"
        )
        await message.answer(
            "👥 <i>Botni guruhingizga qo'shib, do'stlaringiz bilan bellashing:</i>",
            reply_markup=add_to_group_inline(bot_username),
            parse_mode="HTML"
        )
        return

    # Yangi foydalanuvchini bazaga saqlaymiz (keyingi safar qayta so'ralmasligi uchun)
    database.save_user(
        user_id=user_id,
        first_name=name,
        username=user.username,
        phone_number=""
    )
    
    await state.set_state(RegistrationState.waiting_for_contact)
    await message.answer(
        f"Assalomu alaykum, <b>{name}</b>! 👋\n\n"
        f"🧠 <b>Zakovat intellektual o'yini</b> botiga xush kelibsiz!\n\n"
        f"O'yinni boshlash va o'z bilimingizni sinab ko'rish uchun "
        f"iltimos, pastdagi tugma orqali telefon raqamingizni yuboring:",
        reply_markup=contact_keyboard(),
        parse_mode="HTML"
    )


@router.message(RegistrationState.waiting_for_contact, F.contact)
async def process_contact(message: Message, state: FSMContext):
    contact = message.contact
    user = message.from_user
    user_id = user.id
    is_admin = user_id in ADMIN_IDS
    
    # Telefon raqamni saqlash
    phone = contact.phone_number
    first_name = user.first_name or contact.first_name or "Bilimdon"
    username = user.username
    
    database.save_user(
        user_id=user_id,
        first_name=first_name,
        username=username,
        phone_number=phone
    )
    
    await state.clear()
    
    # Nickname aniqlash
    nickname = f"@{username}" if username else first_name
    
    # Welcome xabari
    welcome_text = (
        f"🎉 <b>Xush kelibsiz, {nickname}!</b>\n\n"
        f"Siz <b>Zakovat intellektual o'yini</b>da muvaffaqiyatli ro'yxatdan o'tdingiz! 👏\n\n"
        f"O'yin qoidasi oddiy:\n"
        f"1. <b>'❓ Savol olish'</b> tugmasini bosing.\n"
        f"2. Savolga javobingizni matn ko'rinishida yozib yuboring.\n"
        f"3. Agar javobingiz to'g'ri bo'lsa, sizga ball beriladi!\n\n"
        f"Tayyor bo'lsangiz, boshlaymizmi?"
    )
    
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username or "zakovatgazganbot"

    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(is_admin=is_admin),
        parse_mode="HTML"
    )
    await message.answer(
        "👥 <i>Botni guruhingizga qo'shib, do'stlaringiz bilan birga o'ynash uchun pastdagi tugmani bosing:</i>",
        reply_markup=add_to_group_inline(bot_username),
        parse_mode="HTML"
    )


@router.message(RegistrationState.waiting_for_contact)
async def process_contact_invalid(message: Message):
    await message.answer(
        "⚠️ Iltimos, pastdagi <b>'📱 Telefon raqamni yuborish'</b> tugmasini bosing:",
        reply_markup=contact_keyboard(),
        parse_mode="HTML"
    )
