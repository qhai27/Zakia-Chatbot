# nlp_processor.py

import re
import json
from difflib import SequenceMatcher
from gemini_client import ask_gemini


class NLPProcessor:

    def __init__(self):
        self.training_pairs = []
        self.keyword_index = {}

    # =========================================================
    # 🔥 MAIN INTENT ENGINE — HYBRID
    # =========================================================
    def analyze_user_intent(self, user_message):
        """
        1. Try Gemini (semantic intent detection)
        2. If failed → fallback to rule-based
        """
        gemini_intent = self.analyze_user_intent_gemini(user_message)

        if gemini_intent:
            return gemini_intent

        return self.simple_intent_detection(user_message)

    # =========================================================
    # ✨ GEMINI INTENT DETECTION (UTAMA)
    # =========================================================
    def analyze_user_intent_gemini(self, msg):
        prompt = f"""
Anda ialah modul NLP untuk Chatbot Zakat Kedah (ZAKIA). 
Tugas anda ialah mengenal pasti intent pengguna.

Pastikan output anda adalah FORMAT JSON SAHAJA seperti di bawah:

{{
  "is_greeting": true/false,
  "is_thanks": true/false,
  "is_goodbye": true/false,
  "is_followup": true/false,
  "category": "fitrah | pendapatan | emas | perniagaan | KWSP | harta | am | lain",
  "language": "malay" atau "english",
  "sentiment": "positive | neutral | negative"
}}

Contoh kategori:
- gaji, elaun, side income → "pendapatan"
- emas, perak, simpan emas → "emas"
- bisnes, keuntungan, modal → "perniagaan"
- fitrah → "fitrah"
- kwsp, epf → "KWSP"
- harta, rumah, tanah → "harta"
- soalan umum → "am"

Jawapan mesti 100% JSON tanpa ayat tambahan.

Mesej pengguna:
"{msg}"
"""

        try:
            text = ask_gemini(prompt)
            if not text:
                return None

            # Extract JSON
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                return None

        except Exception as e:
            print("Gemini Intent Error:", e)
            return None

    # =========================================================
    # FALLBACK RULE-BASED INTENT DETECTION
    # =========================================================
    def simple_intent_detection(self, text):
        text = text.lower()

        return {
            "is_greeting": any(w in text for w in ["hi", "hello", "assalam", "salam", "hai"]),
            "is_thanks": any(w in text for w in ["terima kasih", "tq", "thanks", "thank you"]),
            "is_goodbye": any(w in text for w in ["bye", "jumpa", "selamat tinggal"]),
            "is_followup": False,
            "category": "am",
            "language": "malay",
            "sentiment": "neutral"
        }

    # =========================================================
    # FAQ MATCHING ENGINE
    # =========================================================
    def similarity(self, a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def generate_response(self, user_input, faqs, session_id=None, threshold=0.35):
        """
        Cari jawapan FAQ paling hampir berdasarkan similarity score.
        """
        best_match = None
        highest_score = 0

        for faq in faqs:
            score = self.similarity(user_input, faq['question'])
            if score > highest_score:
                highest_score = score
                best_match = faq

        if best_match and highest_score >= threshold:
            return {
                "reply": best_match['answer'],
                "matched_question": best_match['question'],
                "confidence": float(highest_score),
                "confidence_level": "high" if highest_score > 0.75 else "medium",
                "category": best_match.get("category", "Unknown")
            }

        return {
            "reply": "Maaf, saya kurang pasti tentang soalan itu. Boleh jelaskan sedikit lagi?",
            "matched_question": None,
            "confidence": float(highest_score),
            "confidence_level": "low",
            "category": "Unknown"
        }

    # =========================================================
    def get_conversation_insights(self, session_id):
        return {}
