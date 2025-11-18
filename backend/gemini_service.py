"""
Gemini Service - Fixed for Free API Keys
Uses gemini-1.5-flash which is available on free tier
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

        # Models that work with your API key (from diagnostic results)
        models_to_try = [
            "gemini-2.0-flash",                    # ✅ WORKS! (Best option)
            "gemini-2.0-flash-001",                # ✅ WORKS! (Alternative)
            "gemini-2.5-flash-lite-preview-06-17", # ✅ WORKS! (Lighter version)
        ]

        self.model = None
        self.model_name = None

        print("🔍 Testing Gemini models for free API key...")

        for model_name in models_to_try:
            try:
                print(f"   Trying {model_name}...")
                test_model = genai.GenerativeModel(model_name)

                # Test with a simple prompt
                response = test_model.generate_content(
                    "Say 'Hello' if you can read this.",
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=100,
                    )
                )
                
                if response.text:
                    self.model = test_model
                    self.model_name = model_name
                    print(f"✅ Successfully connected to: {model_name}")
                    break

            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    print(f"   ❌ {model_name} not available")
                elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    print(f"   ⚠️ {model_name} quota exceeded")
                else:
                    print(f"   ❌ {model_name} error: {error_msg[:100]}")

        if not self.model:
            raise ValueError(
                "❌ No Gemini models available.\n"
                "Solutions:\n"
                "1. Get a NEW API key from: https://makersuite.google.com/app/apikey\n"
                "2. Ensure you're using a Google account\n"
                "3. Check if API is enabled in your Google Cloud project\n"
                "4. Verify your API key is not expired"
            )

        self.system_context = (
            "Anda adalah ZAKIA, chatbot rasmi Lembaga Zakat Negeri Kedah (LZNK).\n"
            "- Jawab dalam Bahasa Melayu yang mudah difahami\n"
            "- Jangan tambah fakta zakat yang tidak ada dalam FAQ\n"
            "- Jika tidak pasti, minta pengguna jelaskan atau hubungi LZNK\n"
            "- Nada mesra, profesional dan ringkas (2-4 ayat)\n"
            "- Jangan buat ayat yang terlalu panjang\n"
        )

        print(f"🎉 Gemini initialized with model: {self.model_name}")

    def enhance_faq_response(self, user_question: str, faq_answer: str, context: dict = None) -> str:
        """
        Enhance FAQ answer to be more natural and conversational
        """
        try:
            prompt = f"""
{self.system_context}

Soalan pengguna:
{user_question}

Jawapan FAQ rasmi:
{faq_answer}

Tugas:
- Hasilkan versi jawapan yang lebih natural & mesra
- MESTI kekalkan semua fakta dari FAQ 100%
- Jangan tambah maklumat baru yang tidak ada dalam FAQ
- Buat ayat lebih mudah difahami
- Jawab dalam 2-4 ayat sahaja
- Bahasa Melayu yang jelas

Jawapan:
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                )
            )
            
            answer = response.text.strip()

            # Safety check - ensure answer is valid
            if len(answer) < 20 or len(answer) > 1000:
                print(f"   ⚠️ Generated answer length unusual ({len(answer)} chars), using FAQ")
                return faq_answer

            return answer

        except Exception as e:
            print(f"   ⚠️ Enhancement error: {e}")
            return faq_answer

    def generate_fallback_response(self, user_question: str, matched_questions=None) -> str:
        """
        Generate helpful fallback when no FAQ matches
        """
        try:
            suggestion_text = ""
            if matched_questions:
                suggestion_text = "\n\nSoalan yang mungkin berkaitan:\n"
                for i, q in enumerate(matched_questions[:3], 1):
                    suggestion_text += f"{i}. {q}\n"

            prompt = f"""
{self.system_context}

Soalan pengguna:
{user_question}

Status: Tiada padanan FAQ yang tepat dijumpai.

Tugas:
- Beri respons sopan bahawa sistem tidak mempunyai jawapan khusus
- JANGAN reka-reka atau tambah maklumat zakat
- Cadangkan pengguna menghubungi LZNK terus: 04-733 6633
- Jika ada soalan berkaitan, cadangkan soalan tersebut
- Ringkas (2-3 ayat sahaja)

{suggestion_text}

Jawapan:
"""

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=400,
                )
            )
            
            answer = response.text.strip()
            
            if len(answer) < 20:
                # Fallback to default message
                return "Maaf, saya tidak pasti tentang soalan ini. Sila hubungi LZNK di 04-733 6633 untuk maklumat lanjut."
            
            return answer

        except Exception as e:
            print(f"   ⚠️ Fallback generation error: {e}")
            default_msg = "Maaf, saya tidak pasti tentang soalan ini. "
            if matched_questions:
                default_msg += f"\n\nAnda mungkin ingin bertanya tentang:\n"
                for i, q in enumerate(matched_questions[:2], 1):
                    default_msg += f"{i}. {q}\n"
            default_msg += "\nSila hubungi LZNK di 04-733 6633 untuk maklumat lanjut."
            return default_msg

    def generate_conversational_response(self, user_message: str, context: str = None) -> str:
        """
        Generate conversational response for greetings, thanks, etc.
        """
        try:
            context_text = f"\nKonteks: {context}" if context else ""
            
            prompt = f"""
{self.system_context}

Mesej pengguna:
{user_message}
{context_text}

Tugas:
- Jawab secara mesra dan ringkas (1-2 ayat sahaja)
- Sesuai untuk salam, ucapan terima kasih, atau perbualan umum
- Jangan tambah hukum zakat atau maklumat teknikal
- Tunjukkan kesediaan untuk membantu

Jawapan:
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=200,
                )
            )
            
            return response.text.strip()

        except Exception as e:
            print(f"   ⚠️ Conversational response error: {e}")
            return "Terima kasih! Ada apa yang boleh saya bantu? 😊"

    def test_connection(self):
        """
        Test if Gemini API is working
        """
        try:
            print("\n🧪 Testing Gemini API connection...")
            
            response = self.model.generate_content(
                "Say exactly: 'API is working!' in Malay",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=50,
                )
            )
            
            result = {
                "success": True,
                "model": self.model_name,
                "response": response.text.strip(),
                "message": "✅ Gemini API connected successfully!"
            }
            
            print(f"   ✅ Response: {result['response']}")
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "model": self.model_name,
                "error": str(e),
                "api_key_ok": bool(self.api_key),
                "message": "❌ API connection failed!",
                "help": "Get new API key from: https://makersuite.google.com/app/apikey"
            }
            print(f"   ❌ Test failed: {e}")
            return error_result