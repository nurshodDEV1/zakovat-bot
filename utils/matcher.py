import re
from difflib import SequenceMatcher

# O'zbek tilida tez-tez tushirib qoldiriladigan yoki qo'shib aytiladigan yordamchi / tavsiflovchi so'zlar
DESCRIPTORS = {
    "okean", "okeani", "kol", "koli", "daryo", "daryosi",
    "shahar", "shahri", "orol", "oroli", "sayyora", "sayyorasi",
    "tog", "togi", "davlat", "davlati", "viloyat", "viloyati",
    "respublika", "respublikasi", "tuman", "tumani", "qita", "qitasi",
    "asari", "kitob", "kitobi", "film", "filmi", "daraxt", "daraxti",
    "xon", "xoni", "amiri", "shoh", "shohi", "podshoh", "podshohi"
}


def normalize_text(text: str) -> str:
    """
    Matnni taqqoslash uchun tozalaydi va normal holatga keltiradi:
    - Kichik harflarga o'tkazadi
    - O'zbekcha tutuq belgilarini (', `, ʻ, ‘) olib tashlaydi
    - Tinish belgilarini olib tashlaydi
    - Ortiqcha probellarni tozalaydi
    """
    if not text:
        return ""
    
    text = text.lower().strip()
    text = re.sub(r"['`ʻ‘ʼ’]", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_descriptors(text: str) -> str:
    """
    Tavsiflovchi qo'shimcha so'zlarni (okeani, ko'li, shahri, oroli kabi) olib tashlaydi.
    Masalan: 'tinch okeani' -> 'tinch', 'baykal koli' -> 'baykal'
    """
    words = [w for w in text.split() if w not in DESCRIPTORS]
    return " ".join(words) if words else text


def calculate_similarity(user_answer: str, correct_answer: str, threshold: float = 90.0) -> tuple[bool, float, str]:
    """
    Foydalanuvchi javobini to'g'ri javob bilan solishtiradi.
    Aqlli taqqoslash:
    1. Aniq moslik
    2. Tavsiflovchi so'zlarsiz moslik (masalan: 'Tinch' vs 'Tinch okeani' -> 100%)
    3. Kalit so'zlar mosligi (masalan: 'Navoiy' vs 'Alisher Navoiy' -> 100%)
    4. Xato bilan yozilganda SequenceMatcher (masalan: 'Alisher Navoi' vs 'Alisher Navoiy' -> 95%)
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
    
    # Foydalanuvchi javobining yordamchi so'zlardan tozalangan varianti
    clean_user = strip_descriptors(norm_user)
    user_words = set(clean_user.split()) if clean_user else set(norm_user.split())
    
    for variant in variants:
        norm_variant = normalize_text(variant)
        if not norm_variant:
            continue
        
        # 1. Aniq to'g'ri kelishi
        if norm_user == norm_variant:
            return True, 100.0, variant
        
        # 2. Descriptorsiz to'liq to'g'ri kelishi (masalan: 'tinch' == 'tinch' ('tinch okeani'dan))
        clean_variant = strip_descriptors(norm_variant)
        if clean_user and clean_variant and clean_user == clean_variant:
            return True, 100.0, variant
            
        variant_words = set(clean_variant.split()) if clean_variant else set(norm_variant.split())
        
        ratio = 0.0
        
        # 3. Foydalanuvchi asosiy kalit so'zni yozgan bo'lsa
        # (masalan: foydalanuvchi 'tinch' yoki 'navoiy' yoki 'temur' yozsa)
        if user_words and variant_words:
            # Agar foydalanuvchi so'zlari variant so'zlari ichida mavjud bo'lsa
            # va faqat descriptorning o'zi bo'lib qolmasa
            if user_words.issubset(variant_words) and not all(w in DESCRIPTORS for w in norm_user.split()):
                ratio = 100.0
            # Agar variant qisqa bo'lib, foydalanuvchi to'liqroq yozgan bo'lsa (variant: 'navoiy', user: 'alisher navoiy')
            elif variant_words.issubset(user_words) and not all(w in DESCRIPTORS for w in norm_variant.split()):
                ratio = 100.0
        
        # 4. SequenceMatcher orqali matn o'xshashligi
        r_full = SequenceMatcher(None, norm_user, norm_variant).ratio() * 100
        r_clean = 0.0
        if clean_user and clean_variant:
            r_clean = SequenceMatcher(None, clean_user, clean_variant).ratio() * 100
            
        # 5. So'zlardagi mayda harfiy xatolar (masalan: 'alisher navoi' vs 'alisher navoiy')
        r_word = 0.0
        if user_words and variant_words:
            word_ratios = [
                SequenceMatcher(None, uw, vw).ratio() * 100
                for uw in user_words
                for vw in variant_words
            ]
            if word_ratios:
                r_word = max(word_ratios)
        
        current_best = max(ratio, r_full, r_clean, r_word)
        
        if current_best > best_ratio:
            best_ratio = current_best
            best_variant = variant
            
    best_percentage = round(best_ratio, 1)
    is_correct = best_percentage >= threshold
    
    return is_correct, best_percentage, best_variant


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    tests = [
        ("tinch", "Tinch okeani", True),
        ("Tinch", "Tinch okeani", True),
        ("tinch okeani", "Tinch okeani", True),
        ("baykal", "Baykal ko'li", True),
        ("navoiy", "Alisher Navoiy", True),
        ("alisher navoi", "Alisher Navoiy", True),
        ("nyuton", "Isaak Nyuton | Nyuton", True),
        ("korsika", "Korsika oroli", True),
        ("yupiter", "Yupiter", True),
        ("amir temur", "Kuch adolatdadir / Rostlik najotdir", False),
        ("kuch adolatdadir", "Kuch adolatdadir / Rostlik najotdir", True),
        ("okean", "Tinch okeani", False), # faqat yordamchi so'z bo'lgani uchun xato
        ("butunlay notugri", "Tinch okeani", False)
    ]
    for u, c, exp in tests:
        corr, pct, var = calculate_similarity(u, c)
        status = "PASS" if corr == exp else "FAIL"
        print(f"[{status}] User: '{u}' vs '{c}' -> {pct}% | Correct: {corr} (Expected: {exp})")

