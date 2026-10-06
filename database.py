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
