"""
Gemini Service - Stable Version for Free API Keys
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in .env")

        genai.configure(api_key=self.api_key)

        # ONLY include stable free models
        models_to_try = [
            "gemini-pro",
            "gemini-pro-vision"
        ]

        self.model = None
        self.model_name = None

        print("🔍 Checking available Gemini models...")

        for model_name in models_to_try:
            try:
                print(f" - Trying {model_name}")
                test_model = genai.GenerativeModel(model_name)

                response = test_model.generate_content("Hello")
                if response.text:
                    self.model = test_model
                    self.model_name = model_name
                    print(f"✅ Using model: {model_name}")
                    break

            except Exception as e:
                print(f"❌ {model_name} not available: {str(e)[:70]}")

        if not self.model:
            raise ValueError("❌ No available Gemini models. Try regenerating your API key.")

        self.system_context = (
            "Anda adalah ZAKIA, chatbot rasmi Lembaga Zakat Negeri Kedah (LZNK).\n"
            "- Jawab dalam Bahasa Melayu\n"
            "- Jangan tambah fakta zakat yang tidak ada dalam FAQ\n"
            "- Jika tidak pasti, minta pengguna jelaskan\n"
            "- Nada mesra, profesional dan ringkas\n"
        )

        print(f"🎉 Gemini initialized successfully with model '{self.model_name}'")

    # -------------------------------------------------------
    def enhance_faq_response(self, user_question: str, faq_answer: str) -> str:
        try:
            prompt = f"""
{self.system_context}

Soalan pengguna:
{user_question}

Jawapan FAQ rasmi:
{faq_answer}

Tugas:
- Hasilkan versi jawapan lebih natural & mesra
- MESTI kekalkan fakta FAQ 100%
- Jangan tambah maklumat baru
- Bahasa Melayu jelas & mudah

Jawapan:
"""
            response = self.model.generate_content(prompt)
            answer = response.text.strip()

            if len(answer) < 20:
                return faq_answer

            return answer

        except:
            return faq_answer

    # -------------------------------------------------------
    def generate_fallback_response(self, user_question: str, matched_questions=None) -> str:
        try:

            suggestion_text = ""
            if matched_questions:
                suggestion_text = "\nSoalan hampir sama:\n"
                for q in matched_questions[:3]:
                    suggestion_text += f"- {q}\n"

            prompt = f"""
{self.system_context}

Soalan pengguna:
{user_question}

Tiada padanan FAQ dijumpai.

Tugas:
- Beri jawapan sopan bahawa jawapan tiada dalam sistem
- Jangan reka-reka maklumat
- Berikan cadangan soalan berkaitan
- Tawarkan pengguna untuk menghubungi LZNK jika perlu

{suggestion_text}

Jawapan:
"""

            response = self.model.generate_content(prompt)
            return response.text.strip()

        except:
            return "Maaf, saya tidak pasti tentang soalan tersebut. Boleh jelaskan lebih lanjut?"

    # -------------------------------------------------------
    def generate_conversational_response(self, user_message: str) -> str:
        try:
            prompt = f"""
{self.system_context}

Mesej pengguna:
{user_message}

Tugas:
- Jawab secara mesra dan ringkas
- Sesuai untuk salam, ucapan terima kasih, atau soalan umum
- Jangan tambah hukum zakat baru

Jawapan:
"""
            response = self.model.generate_content(prompt)
            return response.text.strip()

        except:
            return "Baik! Ada apa lagi yang boleh saya bantu?"

    # -------------------------------------------------------
    def test_connection(self):
        try:
            response = self.model.generate_content("Say 'working' if you can read this.")
            return {
                "success": True,
                "model": self.model_name,
                "response": response.text.strip()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "api_key_ok": bool(self.api_key)
            }
