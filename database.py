import sqlite3
import random
from typing import Optional, List, Dict, Any

DB_NAME = "zakovat.db"

# Dastlabki qiziqarli Zakovat savollari to'plami
DEFAULT_QUESTIONS = [
    {
        "question": "Rivoyatlarga ko'ra, mashhur faylasuf Diogen kunduzi qo'lida chiroq (fonus) yoqib shahar bo'ylab aylanib yurar ekan. Undan 'Nima qilyapsan?' deb so'raganlarida, u nima deb javob bergan?",
        "answer": "Odam qidiryapman / Haqiqiy odamni qidiryapman / Odam izlayapman",
        "explanation": "Diogen 'Men odam qidiryapman' deb javob bergan va jamiyatdagi insoniy fazilatlarning yo'qolib borayotganiga ishora qilgan."
    },
    {
        "question": "Napoleon Bonapart qaysi orolda tug'ilgan?",
        "answer": "Korsika / Korsika oroli",
        "explanation": "Napoleon 1769-yilda O'rta dengizdagi Korsika orolining Ayachcho shahrida tug'ilgan."
    },
    {
        "question": "Yer yuzidagi eng chuqur ko'l qaysi?",
        "answer": "Baykal / Baykal koli",
        "explanation": "Baykal ko'li Rossiyada joylashgan bo'lib, uning eng chuqur nuqtasi 1642 metrni tashkil etadi."
    },
    {
        "question": "Ushbu buyum qadimgi Misrda paydo bo'lgan. Qizig'i shundaki, dastlab undan faqat erkaklar va aslzodalar baland ko'rinish hamda otda yurishda uzangiga yaxshi o'rnashish uchun foydalanishgan. Hozirda esa bu buyum asosan ayollar garderobida uchraydi. Gap nima haqida ketmoqda?",
        "answer": "Poshna / Baland poshnali poyabzal / Baland poshna",
        "explanation": "Baland poshnalar dastlab otliq askarlar uchun uzangini mahkam ushlash maqsadida kashf etilgan."
    },
    {
        "question": "Alisher Navoiy o'zining turkiy tilda yozgan she'rlarida qaysi taxallusni ishlatgan?",
        "answer": "Navoiy",
        "explanation": "Alisher Navoiy turkiy tildagi asarlarida 'Navoiy', forsiy tildagi asarlarida esa 'Foniy' taxalluslaridan foydalangan."
    },
    {
        "question": "Qaysi mashhur olimning boshiga olma tushganidan so'ng butun olam tortishish qonunini kashf qilgan degan afsona bor?",
        "answer": "Isaak Nyuton / Nyuton",
        "explanation": "Ser Isaak Nyuton olma daraxti tagida o'tirganda tortishish kuchi haqida o'ylay boshlagan."
    },
    {
        "question": "Dunyodagi eng katta okean qaysi?",
        "answer": "Tinch okeani",
        "explanation": "Tinch okeani maydoni bo'yicha dunyodagi eng katta va eng chuqur okean hisoblanadi."
    },
    {
        "question": "Shaxmat taxtasida jami nechta oq va qora katak bor?",
        "answer": "64 / 64 ta",
        "explanation": "Shaxmat taxtasi 8x8 o'lchamda bo'lib, jami 64 ta katakdan iborat (32 oq, 32 qora)."
    },
    {
        "question": "Sohibqiron Amir Temurning davlat shiori qanday bo'lgan?",
        "answer": "Kuch adolatdadir / Rostlik najotdir",
        "explanation": "Amir Temur davlat muhri va tangalarida 'Rosti-rusti' (Kuch adolatdadir) shiorini yozdirgan."
    },
    {
        "question": "Quyosh sistemasidagi eng katta sayyora qaysi?",
        "answer": "Yupiter",
        "explanation": "Yupiter Quyosh tizimidagi eng ulkan gigant gaz sayyorasidir."
    },
    {
        "question": "Mashhur 'Mona Liza' (Jokonda) asarining muallifi kim?",
        "answer": "Leonardo da Vinchi / Da Vinchi",
        "explanation": "Asar italiyalik buyuk rassom Leonardo da Vinchi tomonidan chizilgan."
    },
    {
        "question": "Qaysi hayvon suv ichmaydi va butun umri davomida chanqog'ini faqat iste'mol qilgan urug'lari hisobiga qondiradi?",
        "answer": "Kenguru kalamushi / Kenguru kalamush",
        "explanation": "Cho'lda yashovchi kenguru kalamushlari deyarli suv ichmaydi, organizmidagi suvni oziq-ovqatdan oladi."
    }
]


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Ma'lumotlar bazasi va jadvallarni yaratish hamda boshlang'ich savollarni kiritish"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Foydalanuvchilar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                phone_number TEXT,
                score INTEGER DEFAULT 0,
                total_played INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Savollar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                explanation TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Javoblar tarixi jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                user_answer TEXT,
                similarity REAL,
                is_correct INTEGER,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agar savollar bo'lmasa, boshlang'ich savollarni qo'shish
        cursor.execute("SELECT COUNT(*) as count FROM questions")
        count = cursor.fetchone()["count"]
        if count == 0:
            for q in DEFAULT_QUESTIONS:
                cursor.execute(
                    "INSERT INTO questions (question, answer, explanation) VALUES (?, ?, ?)",
                    (q["question"], q["answer"], q["explanation"])
                )
        conn.commit()


def save_user(user_id: int, first_name: str, username: Optional[str], phone_number: str):
    """Foydalanuvchini ro'yxatdan o'tkazish yoki ma'lumotlarini yangilash"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, first_name, username, phone_number)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name,
                username = excluded.username,
                phone_number = excluded.phone_number
        """, (user_id, first_name, username, phone_number))
        conn.commit()


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()


def is_user_registered(user_id: int) -> bool:
    user = get_user(user_id)
    return user is not None and bool(user["phone_number"])


def get_random_question(user_id: Optional[int] = None) -> Optional[sqlite3.Row]:
    """
    Foydalanuvchi hali to'g'ri javob bermagan tasodifiy savolni oladi.
    Agar barchasiga javob bergan bo'lsa, istalgan tasodifiy savolni qaytaradi.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        if user_id:
            # Foydalanuvchi to'g'ri javob bermagan savollar
            cursor.execute("""
                SELECT * FROM questions 
                WHERE id NOT IN (
                    SELECT question_id FROM user_answers 
                    WHERE user_id = ? AND is_correct = 1
                )
                ORDER BY RANDOM() LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                return row
        
        # Agar barcha savollarni yechgan bo'lsa yoki user_id berilmasa:
        cursor.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 1")
        return cursor.fetchone()


def get_question_by_id(question_id: int) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        return cursor.fetchone()


def add_question(question: str, answer: str, explanation: str = "") -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO questions (question, answer, explanation) VALUES (?, ?, ?)",
            (question.strip(), answer.strip(), explanation.strip())
        )
        conn.commit()
        return cursor.lastrowid


def delete_question(question_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        return cursor.rowcount > 0


def get_all_questions() -> List[sqlite3.Row]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions ORDER BY id DESC")
        return cursor.fetchall()


def record_answer(user_id: int, question_id: int, user_answer: str, similarity: float, is_correct: bool):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_answers (user_id, question_id, user_answer, similarity, is_correct)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, question_id, user_answer, similarity, 1 if is_correct else 0))
        
        # Foydalanuvchi statistikasini yangilash
        score_increment = 1 if is_correct else 0
        cursor.execute("""
            UPDATE users 
            SET score = score + ?,
                total_played = total_played + 1
            WHERE user_id = ?
        """, (score_increment, user_id))
        conn.commit()


def get_leaderboard(limit: int = 10) -> List[sqlite3.Row]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT first_name, username, score, total_played 
            FROM users 
            WHERE total_played > 0
            ORDER BY score DESC, total_played ASC 
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()


def get_statistics() -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM questions")
        total_questions = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM user_answers")
        total_answers = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM user_answers WHERE is_correct = 1")
        correct_answers = cursor.fetchone()["count"]
        
        return {
            "total_users": total_users,
            "total_questions": total_questions,
            "total_answers": total_answers,
            "correct_answers": correct_answers
        }


if __name__ == "__main__":
    init_db()
    print("Baza muvaffaqiyatli ishga tushirildi!")
    stats = get_statistics()
    print("Statistika:", stats)
