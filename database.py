import sqlite3
import random
from typing import Optional, List, Dict, Any

DB_NAME = "zakovat.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Ma'lumotlar bazasi va jadvallarni yaratish"""
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
                image_id TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agar jadval avval yaratilgan bo'lsa, image_id ustunini tekshirish va qo'shish
        cursor.execute("PRAGMA table_info(questions)")
        columns = [col["name"] for col in cursor.fetchall()]
        if "image_id" not in columns:
            cursor.execute("ALTER TABLE questions ADD COLUMN image_id TEXT DEFAULT NULL")
        
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

        # Guruhlar jadvali (Guruhlarda avto-savol uchun)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                is_active INTEGER DEFAULT 0,
                interval_seconds INTEGER DEFAULT 180,
                timeout_seconds INTEGER DEFAULT 90,
                current_question_id INTEGER DEFAULT NULL,
                current_answer TEXT DEFAULT NULL,
                current_explanation TEXT DEFAULT '',
                current_image_id TEXT DEFAULT NULL,
                question_sent_at REAL DEFAULT 0,
                last_action_at REAL DEFAULT 0
            )
        """)

        # Guruhdagi foydalanuvchilar ballari jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_scores (
                chat_id INTEGER,
                user_id INTEGER,
                first_name TEXT,
                username TEXT,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        conn.commit()


def clear_all_questions():
    """Bazadagi barcha savollar va javoblar tarixini butunlay o'chirib tashlaydi"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM questions")
        cursor.execute("DELETE FROM user_answers")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('questions', 'user_answers')")
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
    """Foydalanuvchi bazada mavjud bo'lsa True qaytaradi"""
    user = get_user(user_id)
    return user is not None


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


def add_question(question: str, answer: str, explanation: str = "", image_id: Optional[str] = None) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO questions (question, answer, explanation, image_id) VALUES (?, ?, ?, ?)",
            (question.strip(), answer.strip(), explanation.strip(), image_id)
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
        score_increment = 10 if is_correct else 0
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


# ================= GURUH BILAN ISHLASH FUNKSIYALARI =================

def register_or_update_group(chat_id: int, title: str):
    """Guruhni ro'yxatga olish yoki nomini yangilash"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO groups (chat_id, title)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET title = excluded.title
        """, (chat_id, title))
        conn.commit()


def get_group(chat_id: int) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE chat_id = ?", (chat_id,))
        return cursor.fetchone()


def set_group_auto_status(chat_id: int, is_active: bool, title: str = ""):
    """Guruhda avto-savol holatini yoqish yoki o'chirish"""
    import time
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO groups (chat_id, title, is_active, last_action_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET 
                is_active = excluded.is_active,
                title = CASE WHEN excluded.title != '' THEN excluded.title ELSE groups.title END,
                last_action_at = excluded.last_action_at
        """, (chat_id, title, 1 if is_active else 0, time.time()))
        conn.commit()


def set_group_interval(chat_id: int, minutes: int):
    """Savollar orasidagi oraliq vaqtini (daqiqada) belgilash"""
    seconds = max(1, minutes) * 60
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET interval_seconds = ? WHERE chat_id = ?", (seconds, chat_id))
        conn.commit()


def get_active_groups() -> List[sqlite3.Row]:
    """Avto-savol rejimi yoqilgan barcha guruhlarni olish"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups WHERE is_active = 1")
        return cursor.fetchall()


def set_group_current_question(
    chat_id: int, 
    question_id: int, 
    answer: str, 
    explanation: str = "", 
    image_id: Optional[str] = None
):
    """Guruhga hozir yuborilgan faol savolni saqlash"""
    import time
    now = time.time()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE groups 
            SET current_question_id = ?,
                current_answer = ?,
                current_explanation = ?,
                current_image_id = ?,
                question_sent_at = ?,
                last_action_at = ?
            WHERE chat_id = ?
        """, (question_id, answer, explanation, image_id, now, now, chat_id))
        conn.commit()


def clear_group_current_question(chat_id: int):
    """Guruhdagi joriy savolni tozalash va oxirgi amal vaqtini yangilash"""
    import time
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE groups 
            SET current_question_id = NULL,
                current_answer = NULL,
                current_explanation = '',
                current_image_id = NULL,
                question_sent_at = 0,
                last_action_at = ?
            WHERE chat_id = ?
        """, (time.time(), chat_id))
        conn.commit()


def add_group_user_score(chat_id: int, user_id: int, first_name: str, username: Optional[str]) -> int:
    """Guruhdagi foydalanuvchiga +10 ball qo'shish va yangi ballini qaytarish"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO group_scores (chat_id, user_id, first_name, username, score)
            VALUES (?, ?, ?, ?, 10)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                score = score + 10,
                first_name = excluded.first_name,
                username = excluded.username
        """, (chat_id, user_id, first_name, username))
        
        # Foydalanuvchining yangi ballini olish
        cursor.execute("""
            SELECT score FROM group_scores 
            WHERE chat_id = ? AND user_id = ?
        """, (chat_id, user_id))
        row = cursor.fetchone()
        new_score = row["score"] if row else 10
        conn.commit()
        return new_score


def get_group_leaderboard(chat_id: int, limit: int = 10) -> List[sqlite3.Row]:
    """Aynan shu guruhdagi top foydalanuvchilar reytingi"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT first_name, username, score 
            FROM group_scores 
            WHERE chat_id = ?
            ORDER BY score DESC 
            LIMIT ?
        """, (chat_id, limit))
        return cursor.fetchall()


if __name__ == "__main__":
    init_db()
    print("Baza muvaffaqiyatli ishga tushirildi!")
    stats = get_statistics()
    print("Statistika:", stats)
