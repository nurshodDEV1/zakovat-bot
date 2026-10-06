# 🧠 Zakovat Intellektual O'yini Telegram Boti

Ushbu bot Telegram orqali Zakovat intellektual o'yinini o'tkazish uchun mo'ljallangan.

---

## 🚀 Asosiy Imkoniyatlari

1. **Telefon raqami orqali ro'yxatdan o'tish:**
   - Foydalanuvchi `/start` bosganda, `📱 Telefon raqamni yuborish` tugmasi chiqadi.
   - Telefon raqam yuborilgach, bot foydalanuvchini o'zining **nickname** yoki ismi bilan samimiy kutib oladi ("Welcome" xabari).

2. **Savollar va Aqlli Javob Tekshiruvi (90% Qoidasi):**
   - Foydalanuvchi **"❓ Savol olish"** tugmasini bosganda bazadan tasodifiy (random) savol taqdim etiladi.
   - Foydalanuvchi o'z javobini matn ko'rinishida yozadi.
   - Bot foydalanuvchi javobini to'g'ri javob bilan solishtiradi:
     - **90% yoki undan yuqori** o'xshashlik bo'lsa: **TRUE ✅ (To'g'ri javob!)** va +1 ball beriladi.
     - **90% dan kam** bo'lsa: **FALSE ❌ (Noto'g'ri)** deb belgilanadi va to'g'ri javob ko'rsatiladi.
   - Harflardagi mayda xatolar, o'zbekcha tutuq belgilari (`'`, `` ` ``, `ʻ`, `‘`), katta-kichik harflar va tinish belgilari avtomatik to'g'irlanadi.

3. **Guruhlarda Avto-Savol O'yini (Guruh Zakovat):**
   - Botni istalgan Telegram guruhiga qo'shish mumkin.
   - Guruh admini `/start_quiz` buyrug'i orqali avtomatik Zakovat o'yinini yoqadi.
   - Bot har bir belgilangan vaqtda (standart 3 daqiqa) yangi savol (matnli yoki rasmli) yuboradi.
   - Guruh a'zolariga javob berish uchun 90 soniya beriladi.
   - Birinchi bo'lib to'g'ri javob yozgan bilimdon g'olib deb e'lon qilinadi va guruhdagi reytingiga +1 ball qo'shiladi.
   - Agar hech kim topa olmasa, vaqt tugagach to'g'ri javob e'lon qilinadi va oraliq vaqtdan keyin yangi savol keladi.
   - Buyruqlar: `/start_quiz`, `/stop_quiz`, `/interval <daqiqa>`, `/savol`, `/reyting`.

4. **Admin Boshqaruv Paneli (`/admin`):**
   - ➕ **Yangi savol qo'shish:** Matnli yoki rasmli savol, to'g'ri javob va ixtiyoriy izoh kiritish.
   - 📋 **Savollar ro'yxati:** Bazadagi savollarni rasmi bilan ko'rish va inline tugma orqali o'chirish.
   - 🗑 **Barcha savollarni tozalash:** Bazani bitta tugma bilan tozalash.
   - 📊 **Umumiy statistika:** Jami foydalanuvchilar, guruhlar, savollar va berilgan javoblar soni.

5. **Reyting va Profil:**
   - **📊 Mening profilim:** Shaxsiy ball, jami urinishlar va samaradorlik foizi.
   - **🏆 Reyting:** Eng ko'p ball to'plagan Top 10 bilimdonlar ro'yxati.

---

## 🛠 O'rnatish va Ishga Tushirish

### 1. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 2. Sozlamalarni kiritish
Loyihada mavjud bo'lgan [.env](file:///.env) faylini oching va ma'lumotlaringizni kiriting:

```env
# @BotFather dan olingan bot tokeni:
BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Sizning Telegram ID raqamingiz (masalan @userinfobot orqali olishingiz mumkin):
ADMIN_IDS=123456789

# O'xshashlik chegarasi (standart 90%):
SIMILARITY_THRESHOLD=90.0
```

### 3. Botni ishga tushirish
```bash
python main.py
```

---

## 📁 Loyiha Strukturasi

```
zakovat bot/
├── .env                  # Bot token va admin sozlamalari
├── .env.example          # Sozlamalar namunasi
├── config.py             # Konfiguratsiya moduli
├── database.py           # SQLite ma'lumotlar bazasi va CRUD funksiyalar
├── main.py               # Botni ishga tushirish fayli
├── requirements.txt      # Kerakli Python kutubxonalari
├── README.md             # Qo'llanma
├── utils/
│   ├── __init__.py
│   └── matcher.py        # 90% o'xshashlikni hisoblovchi matn solishtirish algoritmi
├── keyboards/
│   ├── __init__.py
│   └── keyboards.py      # Barcha Telegram tugmalari
├── states/
│   ├── __init__.py
│   └── states.py         # FSM holatlari (Registration, Game, Admin)
└── handlers/
    ├── __init__.py
    ├── start.py          # /start va telefon raqam qabul qilish
    ├── game.py           # Savol-javob, 90% tekshiruv, profil va reyting
    └── admin.py          # Admin paneli (savol qo'shish, ko'rish, o'chirish)
```
