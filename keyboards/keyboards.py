from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)

def contact_keyboard() -> ReplyKeyboardMarkup:
    """Telefon raqamni yuborish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Asosiy menyu tugmalari"""
    keyboard = [
        [KeyboardButton(text="❓ Savol olish")],
        [KeyboardButton(text="📊 Mening profilim"), KeyboardButton(text="🏆 Reyting")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="⚙️ Admin panel")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

def in_game_keyboard() -> ReplyKeyboardMarkup:
    """Savolga javob berish jarayonidagi tugmalar"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ O'tkazib yuborish"), KeyboardButton(text="🏠 Bosh menyu")]
        ],
        resize_keyboard=True
    )

def after_answer_keyboard() -> ReplyKeyboardMarkup:
    """Javob berilgandan keyin chiqadigan tugmalar"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Keyingi savol"), KeyboardButton(text="🏠 Bosh menyu")]
        ],
        resize_keyboard=True
    )

def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Admin boshqaruv paneli tugmalari"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi savol qo'shish")],
            [KeyboardButton(text="📋 Savollar ro'yxati"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🏠 Bosh menyu")]
        ],
        resize_keyboard=True
    )

def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Amalni bekor qilish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def question_delete_inline(question_id: int) -> InlineKeyboardMarkup:
    """Savolni o'chirish uchun inline tugma"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Savolni o'chirish",
                    callback_data=f"del_q:{question_id}"
                )
            ]
        ]
    )

remove_keyboard = ReplyKeyboardRemove()
