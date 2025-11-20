"""
Gemini Service - SMART MODE
This module handles interaction with Google Gemini via the genai SDK.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
import re

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in .env")

        genai.configure(api_key=self.api_key)

        # Try available models
        models_to_try = [
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.5-flash-lite-preview-06-17",
        ]

        self.model = None
        self.model_name = None

        print("🔍 Testing Gemini models...")

        for model_name in models_to_try:
            try:
                test_model = genai.GenerativeModel(model_name)
                response = test_model.generate_content(
                    "Say 'OK'",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=50,
                    )
                )
                
                if response.text:
                    self.model = test_model
                    self.model_name = model_name
                    print(f"✅ Connected to: {model_name}")
                    break

            except Exception as e:
                print(f"   ❌ {model_name}: {str(e)[:100]}")

        if not self.model:
            raise ValueError("❌ No Gemini models available")

        # System context for FAQ enhancement (STRICT)
        self.strict_context = """Anda adalah ZAKIA, chatbot rasmi Lembaga Zakat Negeri Kedah (LZNK).

🔴 PERATURAN ULTRA KETAT - FAQ MODE:

1. HANYA tulis semula FAQ dalam bahasa yang lebih mesra
2. WAJIB kekalkan SEMUA fakta, nombor, dan hukum dari FAQ 100%
3. JANGAN tambah maklumat baru yang tidak ada dalam FAQ
4. JANGAN ubah nombor atau peratusan
5. JANGAN guna: "biasanya", "mungkin", "kadang-kadang"
6. Gunakan emoji sesuai (😊 💰 📞 ✅ 🙏)
7. Ringkas (2-4 ayat)

CONTOH BETUL:
FAQ: "Nisab zakat pendapatan RM15,000 setahun, kadar 2.5%"
ANDA: "Nisab zakat pendapatan ialah RM15,000 setahun ya 😊 Kalau sampai jumlah ni, kena bayar 2.5% dari pendapatan. 💰✅"
"""

        # System context for answering questions WITHOUT FAQ (KNOWLEDGEABLE)
        self.smart_context = """Anda adalah ZAKIA, chatbot pakar zakat dari Lembaga Zakat Negeri Kedah (LZNK).

PERATURAN SMART MODE - TIADA FAQ:

ANDA BOLEH:
1. Jawab soalan am tentang zakat berdasarkan hukum Islam yang sahih
2. Terangkan konsep zakat (fitrah, pendapatan, perniagaan, emas, wang simpanan)
3. Bagi contoh pengiraan zakat yang betul
4. Terangkan syarat wajib zakat, nisab, haul
5. Gunakan pengetahuan zakat yang betul dan tepat
6. Berikan maklumat berguna dan berfakta

ANDA MESTI:
1. Gunakan pengetahuan zakat Islam yang sahih dan tepat
2. Kalau ada nombor/kadar, pastikan tepat mengikut hukum zakat
3. Terang dengan jelas dan mudah faham
4. Mesra, sopan, professional
5. Ringkas tapi lengkap (3-5 ayat)
6. Jika soalan sangat spesifik tentang LZNK Kedah, cadangkan hubungi: 04-733 6633

CONTOH BETUL (Smart Mode):
Soalan: "Apa itu haul dalam zakat?"
Jawapan: "Haul bermaksud tempoh masa genap setahun (12 bulan Hijrah) kita miliki harta ya 😊 Kalau harta kita mencapai nisab dan bertahan selama haul, barulah wajib bayar zakat. Ini syarat penting untuk zakat harta seperti wang simpanan dan emas. 💰✅"

Soalan: "Macam mana kira zakat emas?"
Jawapan: "Zakat emas wajib bila ada 85 gram ke atas dan dimiliki setahun (haul) 😊 Kadar zakatnya 2.5% dari nilai emas tersebut. Contoh: Kalau ada 100 gram emas, zakat = 100g × 2.5% = 2.5 gram emas (atau nilai wang). 💰✅"

JANGAN BUAT:
Bagi maklumat yang tidak tepat atau ragu-ragu
Guna "saya tidak pasti" untuk soalan zakat asas
Tolak jawab soalan am tentang zakat yang anda tahu
"""

        print(f"🎉 Gemini initialized (SMART MODE - Can answer zakat questions)")

    def enhance_faq_response(self, user_question: str, faq_answer: str, context: dict = None) -> str:
        """
        Enhance FAQ - STRICT mode (kekalkan fakta FAQ 100%)
        """
        try:
            prompt = f"""{self.strict_context}

SOALAN PENGGUNA:
{user_question}

JAWAPAN FAQ RASMI (SUMBER MAKLUMAT SAHAJA):
{faq_answer}

TUGAS:
1. Tulis SEMULA dengan bahasa lebih mesra
2. WAJIB kekalkan 100% SEMUA nombor, nilai, peratusan dari FAQ
3. JANGAN tambah fakta baru
4. Maksimum 3-4 ayat
5. Tambah emoji sesuai

JAWAB SEKARANG:
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Very low for FAQ
                    max_output_tokens=400,
                )
            )
            
            answer = response.text.strip()

            # STRICT validation for FAQ mode
            if not answer or len(answer) < 15:
                return faq_answer
            
            # Check forbidden phrases
            forbidden = ['biasanya', 'mungkin', 'kadang', 'lazimnya', 'saya rasa']
            if any(word in answer.lower() for word in forbidden):
                print(f"   ⚠️ Forbidden phrase detected, using FAQ")
                return faq_answer
            
            # Verify numbers match
            faq_numbers = set(re.findall(r'\d+(?:\.\d+)?', faq_answer))
            answer_numbers = set(re.findall(r'\d+(?:\.\d+)?', answer))
            
            if answer_numbers - faq_numbers:
                print(f"   ⚠️ New numbers detected, using FAQ")
                return faq_answer

            return answer

        except Exception as e:
            print(f"   ⚠️ Enhancement error: {e}")
            return faq_answer

    def answer_zakat_question(self, user_question: str, matched_questions=None) -> str:
        """
        SMART MODE: Answer zakat questions using Gemini's knowledge
        This is called when NO FAQ matches
        """
        try:
            suggestion_text = ""
            if matched_questions:
                suggestion_text = "\n\nSOALAN BERKAITAN DALAM FAQ:\n"
                for i, q in enumerate(matched_questions[:3], 1):
                    suggestion_text += f"{i}. {q}\n"

            prompt = f"""{self.smart_context}

SOALAN PENGGUNA:
{user_question}

STATUS: Tiada FAQ yang sepadan - gunakan pengetahuan zakat anda

TUGAS:
1. Jawab soalan ini berdasarkan pengetahuan zakat Islam yang sahih
2. Terangkan dengan jelas, mudah faham
3. Kalau melibatkan nombor/kadar, pastikan tepat
4. Mesra dan professional
5. 3-5 ayat (ringkas tapi lengkap)
6. Tambah emoji yang sesuai
7. Jika soalan sangat spesifik tentang LZNK Kedah, cadangkan hubungi 04-733 6633

{suggestion_text}

PENTING:
- Jawab dengan yakin berdasarkan hukum zakat yang betul
- Jangan kata "saya tidak pasti" untuk soalan zakat asas
- Bagi jawapan yang berguna dan berfakta

JAWAB SEKARANG (gunakan pengetahuan zakat anda):
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,  # Higher for creative but accurate answers
                    max_output_tokens=600,
                )
            )
            
            answer = response.text.strip()
            
            # Basic validation
            if len(answer) < 20:
                return self._get_default_fallback(matched_questions)
            
            # Add emoji if missing
            emojis = ['😊', '💰', '✅', '📞', '🙏', '💡']
            if not any(emoji in answer for emoji in emojis):
                answer += " 😊"
            
            # Add LZNK contact if answer is very specific to procedures
            if 'lznk' not in answer.lower() and any(word in user_question.lower() for word in ['kedah', 'lznk', 'pejabat', 'tempat']):
                answer += "\n\nUntuk maklumat lanjut tentang LZNK Kedah, hubungi 04-733 6633 ya! 📞"
            
            return answer

        except Exception as e:
            print(f"   ⚠️ Smart answer error: {e}")
            return self._get_default_fallback(matched_questions)
    
    def _get_default_fallback(self, matched_questions=None) -> str:
        """Safe default fallback - only when Gemini fails"""
        msg = "Maaf, saya tidak pasti tentang soalan ini 😊\n\n"
        
        if matched_questions:
            msg += "Anda mungkin ingin bertanya:\n"
            for i, q in enumerate(matched_questions[:2], 1):
                msg += f"{i}. {q}\n"
            msg += "\n"
        
        msg += "Untuk maklumat tepat, sila hubungi LZNK di 04-733 6633 ya! 😊📞"
        return msg

    def generate_conversational_response(self, user_message: str, context: str = None) -> str:
        """Conversational response for greetings, thanks, etc"""
        try:
            context_text = f"\nKonteks: {context}" if context else ""
            
            prompt = f"""Anda adalah ZAKIA dari LZNK.

MESEJ: {user_message}{context_text}

TUGAS:
- Balas mesra (1-2 ayat)
- JANGAN bagi nasihat zakat (ini bukan soalan zakat)
- Gunakan emoji 😊👋🙏

JAWAB:
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.6,
                    max_output_tokens=150,
                )
            )
            
            answer = response.text.strip()
            
            # Add emoji if missing
            emojis = ['😊', '👋', '🙏', '✅']
            if not any(e in answer for e in emojis):
                answer += " 😊"
            
            return answer

        except Exception as e:
            return "Terima kasih! Ada apa yang boleh saya bantu? 😊"

    def test_connection(self):
        """Test Gemini connection"""
        try:
            response = self.model.generate_content(
                "Say 'API berfungsi!' in Malay",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=30,
                )
            )
            
            return {
                "success": True,
                "model": self.model_name,
                "response": response.text.strip(),
                "message": "✅ Gemini connected (SMART MODE)!"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "❌ Connection failed!"
            }