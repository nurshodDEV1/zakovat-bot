import re
from difflib import SequenceMatcher

def normalize_text(text: str) -> str:
    """
    Matnni taqqoslash uchun tozalaydi va normal holatga keltiradi:
    - Kichik harflarga o'tkazadi
    - O'zbekcha tutuq belgilarini (', `, ʻ, ‘) standartlashtiradi yoki olib tashlaydi
    - Tinish belgilarini olib tashlaydi
    - Ortiqcha probellarni tozalaydi
    """
    if not text:
        return ""
    
    text = text.lower().strip()
    
    # O'zbekcha tutuq belgilarini birlashtirish
    text = re.sub(r"['`ʻ‘ʼ’]", "", text)
    
    # Tinish belgilari va keraksiz belgilarni olib tashlash
    text = re.sub(r"[^\w\s]", " ", text)
    
    # Ortiqcha probellarni bittaga keltirish
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def calculate_similarity(user_answer: str, correct_answer: str, threshold: float = 90.0) -> tuple[bool, float, str]:
    """
    Foydalanuvchi javobini to'g'ri javob bilan solishtiradi.
    To'g'ri javobda bir nechta variantlar bo'lishi mumkin (masalan: "Amir Temur | Temurbek | Sohibqiron")
    
    Qaytaradi:
    - is_correct (bool): Foiz threshold (90%) dan katta yoki teng bo'lsa True
    - best_percentage (float): Eng yuqori o'xshashlik foizi (0.0 - 100.0)
    - matched_variant (str): Eng yaqin kelgan to'g'ri javob varianti
    """
    norm_user = normalize_text(user_answer)
    if not norm_user:
        return False, 0.0, correct_answer
    
    # Variantlarni ajratib olish ( | yoki / yoki ; bo'yicha)
    variants = [v.strip() for v in re.split(r"[|/;]", correct_answer) if v.strip()]
    if not variants:
        variants = [correct_answer.strip()]
    
    best_ratio = 0.0
    best_variant = variants[0]
    
    for variant in variants:
        norm_variant = normalize_text(variant)
        if not norm_variant:
            continue
        
        # Aniq tenglik
        if norm_user == norm_variant:
            return True, 100.0, variant
        
        # SequenceMatcher orqali o'xshashlikni hisoblash
        ratio = SequenceMatcher(None, norm_user, norm_variant).ratio() * 100
        
        # Agar to'g'ri javob qisqa bo'lib, foydalanuvchi javobida to'liq bo'lsa yoki aksincha
        # Masalan: to'g'ri javob "Navoiy", foydalanuvchi "Alisher Navoiy" yozsa
        words_user = set(norm_user.split())
        words_variant = set(norm_variant.split())
        if words_variant and words_variant.issubset(words_user):
            # Kalit so'z to'liq qatnashgan
            token_ratio = (len(words_variant) / len(words_user)) * 100
            if token_ratio >= 90.0:
                ratio = max(ratio, 95.0)
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_variant = variant
            
    best_percentage = round(best_ratio, 1)
    is_correct = best_percentage >= threshold
    
    return is_correct, best_percentage, best_variant


if __name__ == "__main__":
    # Testlar
    tests = [
        ("amir temur", "Amir Temur", True),
        ("Alisher Navoi", "Alisher Navoiy", True), # bitta harf tushib qolsa ham ~92%
        ("Toshkent shahri", "Toshkent", False),
        ("ozbekiston", "O'zbekiston", True),
        ("Samarqand", "Samarqand / Samarqand shahri", True),
        ("Nyuton", "Isaak Nyuton | Nyuton", True),
        ("butunlay notugri javob", "Amir Temur", False),
    ]
    for user_ans, corr_ans, expected in tests:
        correct, perc, variant = calculate_similarity(user_ans, corr_ans)
        print(f"User: '{user_ans}' vs '{corr_ans}' -> {perc}% | To'g'rimi: {correct} (Kutilgan: {expected})")
