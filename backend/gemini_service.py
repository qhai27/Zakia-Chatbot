"""
Gemini Service - SMART MODE for ZAKIA Chatbot
Improved prompts, validation, and response quality
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

        # Try models in order of preference
        models_to_try = [
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
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

        # Enhanced system context for FAQ mode
        self.strict_context = """Anda adalah ZAKIA, chatbot rasmi Lembaga Zakat Negeri Kedah (LZNK).

🎯 MISI ANDA: Bantu pengguna faham zakat dengan cara yang MESRA dan MUDAH
🗣️ Anda boleh faham dialek Kedah dan (jika sesuai) jawab menggunakan sedikit slang Kedah supaya lebih akrab dengan pengguna Kedah.
📋 PERATURAN KETAT - FAQ MODE:

WAJIB IKUT:
✅ Tulis semula FAQ dengan bahasa yang lebih mesra dan mudah faham
✅ KEKALKAN 100% semua fakta, nombor, kadar, dan hukum dari FAQ
✅ Gunakan emoji yang sesuai untuk setiap topik
✅ Format dalam bentuk point atau ayat pendek (mudah dibaca)
✅ Ringkas tetapi lengkap (2-4 ayat)

DILARANG:
❌ Tambah maklumat baru yang TIDAK ada dalam FAQ
❌ Ubah atau tukar nombor, peratusan, atau nilai
❌ Guna kata: "biasanya", "mungkin", "kadang-kadang", "lebih kurang"
❌ Buat ayat panjang yang susah faham

🎨 EMOJI GUIDE:
💰 - wang, zakat, bayaran
📞 - hubungi, telefon
✅ - betul, wajib, boleh
❌ - salah, tidak boleh
📝 - maklumat, dokumen
🙏 - doa, ibadah
✨ - penting, khas
💡 - tips, idea
🏦 - bank, pembayaran
📱 - online, apps

✨ CONTOH FORMAT TERBAIK:

FAQ Original: "Nisab zakat pendapatan adalah RM15,000 setahun. Kadar zakat ialah 2.5% daripada pendapatan bersih."

JAWAPAN ANDA:
"Zakat pendapatan wajib bila pendapatan anda capai RM15,000 setahun ya 😊

📌 Kadar: 2.5% dari pendapatan bersih
📌 Contoh: Gaji RM20,000/tahun → Zakat = RM500

Senang je kan? 💰✅"

FAQ Original: "Untuk bayar zakat, boleh datang ke pejabat LZNK atau bayar online melalui portal."

JAWAPAN ANDA:
"Mudah je nak bayar zakat! Ada 2 cara 😊

1️⃣ Datang ke pejabat LZNK
2️⃣ Bayar online di portal rasmi

Pilih yang paling senang untuk anda! 💻✅"
"""

        # Enhanced Smart Mode context
        self.smart_context = """Anda adalah ZAKIA, chatbot pakar zakat dari Lembaga Zakat Negeri Kedah (LZNK).

🎯 MISI ANDA: Jadi penasihat zakat yang MESRA, TEPAT, dan MEMBANTU

💡 SMART MODE - Tiada FAQ Match:
🗣️ Model juga perlu faham Bahasa Kedah dan boleh membalas menggunakan slang Kedah bila user guna dialek tersebut.
KUASA ANDA:
✅ Jawab soalan am tentang zakat berdasarkan hukum Islam yang sahih
✅ Terangkan jenis-jenis zakat (fitrah, pendapatan, perniagaan, emas, pertanian, saham)
✅ Bagi pengiraan zakat yang betul dengan contoh jelas
✅ Jelaskan syarat wajib zakat, nisab, haul, dan kadar
✅ Bantu pengguna faham konsep zakat dengan mudah
✅ Bagi nasihat praktikal dan berguna
✅ Jawab soalan kompleks dengan terperinci

PANDUAN JAWAPAN:
1️⃣ Mulakan dengan penjelasan ringkas dan jelas
2️⃣ Sertakan contoh pengiraan jika relevan
3️⃣ Gunakan emoji untuk mudah faham
4️⃣ Format dalam bentuk point (mudah dibaca)
5️⃣ Panjang: 3-6 ayat (bergantung kompleksiti soalan)
6️⃣ Akhiri dengan tawaran bantuan lanjut jika perlu

📊 MAKLUMAT ZAKAT STANDARD (gunakan bila perlu):

ZAKAT PENDAPATAN:
• Nisab: Ikut harga emas semasa yang ditetapkan LZNK
• Kadar: 2.5% dari pendapatan bersih
• Contoh: Gaji RM36,000/tahun → Zakat = RM900/tahun

ZAKAT EMAS:
• Nisab: 85 gram emas
• Haul: 1 tahun (12 bulan Hijrah)
• Kadar: 2.5% dari nilai emas

ZAKAT WANG SIMPANAN:
• Nisab: Setara nilai 85g emas (lebih kurang RM18,000+)
• Haul: 1 tahun
• Kadar: 2.5% dari jumlah simpanan

ZAKAT PERNIAGAAN:
• Nisab: Setara nilai 85g emas
• Haul: 1 tahun
• Kadar: 2.5% dari (aset semasa + untung - hutang)

ZAKAT FITRAH:
• Wajib: Setiap Muslim (dewasa & kanak-kanak)
• Masa: Bulan Ramadan (sebelum Hari Raya)
• Kadar: Ikut penetapan LZNK setiap tahun

✨ CONTOH JAWAPAN BERKUALITI:

Soalan: "Apa itu haul dalam zakat?"

JAWAPAN TERBAIK:
"Haul tu maksudnya tempoh genap SETAHUN (12 bulan Hijrah) kita pegang harta tersebut 😊

📌 Syarat penting untuk zakat harta seperti:
• Wang simpanan 💰
• Emas 👑
• Harta perniagaan 🏪

Contoh: Kalau anda ada simpanan RM20,000 pada 1 Jan 2024, kena tunggu sampai 1 Jan 2025 (genap setahun) baru wajib kira zakat.

Senang faham kan? Ada soalan lagi? 😊✅"

Soalan: "Macam mana kira zakat pendapatan?"

JAWAPAN TERBAIK:
"Senang je kira zakat pendapatan! 😊 Saya tunjuk cara:

📝 FORMULA:
Zakat = Pendapatan Bersih × 2.5%

💡 CONTOH PENGIRAAN:
Gaji setahun: RM48,000
Tolak potongan: RM8,000 (KWSP, cukai, etc)
Pendapatan bersih: RM40,000

Zakat = RM40,000 × 2.5% = RM1,000/tahun

✅ Syarat wajib: Pendapatan bersih mesti capai nisab RM15,456/tahun

Dah faham? Cuba kira untuk pendapatan anda! 💰😊"

Soalan: "Zakat saham macam mana?"

JAWAPAN TERBAIK:
"Zakat saham ada 2 cara bergantung niat pelaburan anda 😊

1️⃣ PELABURAN JANGKA PANJANG (Simpan dapat dividen):
• Zakat dari dividen sahaja: 10%
• Contoh: Dapat dividen RM5,000 → Zakat RM500

2️⃣ PELABURAN JUAL BELI (Trading):
• Zakat dari nilai saham + keuntungan: 2.5%
• Kira selepas genap 1 tahun (haul)
• Contoh: Nilai saham RM30,000 → Zakat RM750

📌 TIPS: Pastikan nilai saham capai nisab (setara 85g emas)

Ada portfolio saham? Cuba kira mengikut kategori anda! 📈💰"

🎯 BILA SOALAN SPESIFIK TENTANG LZNK KEDAH:
Jika soalan tentang prosedur khusus, lokasi pejabat, atau perkhidmatan LZNK yang anda tak pasti, cadangkan:

"Untuk maklumat terperinci tentang [topik], saya cadangkan hubungi terus LZNK Kedah ya 😊

📞 Talian Bebas Tol: 1800-88-1740
📱 WhatsApp: 0194181740.
🌐 Portal: https://www.zakatkedah.com.my/

Mereka boleh bantu dengan lebih detail! ✅"

❌ JANGAN BUAT:
• Jawab dengan ragu-ragu ("mungkin", "saya rasa")
• Bagi nombor atau kadar yang tidak tepat
• Tolak jawab soalan asas tentang zakat
• Buat pengguna keliru dengan penjelasan berbelit
• Lupa sertakan emoji (buat mesej jadi kering!)

💪 INGAT: Anda adalah PAKAR zakat yang mesra dan membantu!

🗣️ Balas mengguna sedikit SLANG KEDAH bila sesuai dan pengguna menulis dalam dialek.
"""

        print(f"🎉 Gemini initialized: {self.model_name} (ENHANCED MODE)")

    def _convert_to_kedah_slang(self, text: str) -> str:
        """Simple word-level replacement to give replies a Kedah flavour."""
        if not text:
            return text
        # Map standard Malay words to Kedah-style slang equivalents
        result = text
        slang_map = {
            # Kata ganti nama
            'anda': 'hang',
            'awak': 'hang',
            'kamu': 'hang',
            'engkau': 'hang',
            'saya': 'kami',         
            'aku': 'aku',
            'kita': 'kite',
            'kami': 'kami',
            'mereka': 'depa',
            'dia': 'dia',           

            # Kata tanya
            'apa': 'ape',
            'mengapa': 'pasai apa',
            'kenapa': 'pasai apa',
            'bagaimana': 'lagu mano',
            'macam mana': 'lagu mano',
            'mana': 'mano',
            'bila': 'bila',
            'berapa': 'berapa',

            # Kata kerja umum
            'boleh': 'bleh',
            'hendak': 'nak',
            'mahu': 'nak',
            'pergi': 'pi',
            'datang': 'mai',
            'balik': 'balik',
            'tunggu': 'tunggu sat',
            'ambil': 'ambik',
            'beri': 'bagi',
            'memberikan': 'bagi',
            'minta': 'mintak',
            'buat': 'buat',
            'cakap': 'cakap',
            'kata': 'kata',

            # Kata hubung / sendi
            'kerana': 'sebab',
            'sebab': 'pasai',
            'kepada': 'kat',
            'pada': 'kat',
            'dengan': 'deng',
            'untuk': 'untuk',
            'dari': 'dari',

            # Penafian
            'tidak': 'dak',
            'tak': 'dak',
            'bukan': 'bukan',

            # Masa
            'nanti': 'satgi',
            'sekarang': 'la ni',
            'tadi': 'tadi',
            'sudah': 'dah',
            'belum': 'lum',
            'selalu': 'slalu',

            # Tambahan
            'sahaja': 'ja',
            'saja': 'ja',
            'sangat': 'sangat',
            'betul': 'betoi',
            'kecil': 'kecik',
            'besar': 'besaq',
            'rumah': 'rumoh',
            'kena': 'kene',
            'tengok': 'tengok',
            'lihat': 'tengok',
            'cepat': 'cepat',
            'lambat': 'lambat',
        }
        for std, slang in slang_map.items():
            result = re.sub(rf"\b{std}\b", slang, result, flags=re.IGNORECASE)
        return result


    def enhance_faq_response(self, user_question: str, faq_answer: str, context: dict = None) -> str:
        """
        Enhanced FAQ mode with better formatting and validation
        """
        try:
            # Add context if available
            context_text = ""
            if context and isinstance(context, dict):
                if context.get('matched_keyword'):
                    context_text = f"\n\nKata kunci: {context['matched_keyword']}"
                if context.get('confidence'):
                    context_text += f"\nKeyakinan: {context['confidence']}"

            prompt = f"""{self.strict_context}

📥 SOALAN PENGGUNA:
"{user_question}"

📚 JAWAPAN FAQ RASMI (Sumber maklumat - KEKALKAN semua fakta):
{faq_answer}
{context_text}

🎯 TUGAS ANDA:
1. Tulis semula dengan bahasa yang lebih mesra dan mudah faham
2. WAJIB kekalkan SEMUA nombor, nilai, dan fakta 100%
3. Format dalam bentuk point atau ayat pendek
4. Maksimum 4-5 ayat (jangan panjang sangat)
5. Gunakan emoji yang sesuai untuk topik ini
6. Pastikan pengguna faham dengan mudah

💬 JAWAPAN MESRA ANDA:
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Low for FAQ accuracy
                    max_output_tokens=500,
                    top_p=0.8,
                    top_k=40,
                )
            )
            
            answer = response.text.strip()            # convert to Kedah slang before returning
            answer = self._convert_to_kedah_slang(answer)
            # Enhanced validation
            if not self._validate_faq_answer(answer, faq_answer):
                print("   ⚠️ Validation failed, using FAQ")
                return self._format_basic_faq(faq_answer)
            
            # Ensure minimum quality
            if len(answer) < 20 or not any(emoji in answer for emoji in ['😊', '💰', '✅', '📌', '💡', '🙏']):
                return self._format_basic_faq(faq_answer)
            
            return answer

        except Exception as e:
            print(f"   ⚠️ Enhancement error: {e}")
            return self._format_basic_faq(faq_answer)

    

    def generate_conversational_response(self, user_message: str, context: str = None) -> str:
        """Enhanced conversational responses"""
        try:
            context_text = f"\nKonteks: {context}" if context else ""
            
            # Detect conversation type
            msg_lower = user_message.lower()
            
            if any(word in msg_lower for word in ['hai', 'hello', 'hi', 'assalam']):
                response_type = "greeting"
            elif any(word in msg_lower for word in ['terima kasih', 'thanks', 'tq', 'syukur']):
                response_type = "thanks"
            elif any(word in msg_lower for word in ['bye', 'selamat tinggal', 'jumpa lagi']):
                response_type = "farewell"
            else:
                response_type = "general"
            
            prompt = f"""Anda adalah ZAKIA dari LZNK Kedah 😊

MESEJ: "{user_message}"{context_text}
JENIS: {response_type}

TUGAS:
- Balas dengan MESRA dan RINGKAS (1-2 ayat sahaja)
- Gunakan emoji yang sesuai 😊💙🙏
- JANGAN bagi nasihat zakat (ini bukan soalan zakat)
- Tunjukkan anda sedia membantu

CONTOH BALAS:
Greeting: "Waalaikumussalam! 😊 Selamat datang ke ZAKIA. Ada apa yang boleh saya bantu hari ni?"
Thanks: "Sama-sama! 😊 Seronok dapat bantu. Ada soalan lain?"
Farewell: "Jumpa lagi! 🙏 Jangan segan bertanya bila-bila masa ya 😊"

BALAS SEKARANG:
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=150,
                )
            )
            
            answer = response.text.strip()
            
            # Ensure has emoji
            if not any(e in answer for e in ['😊', '🙏', '💙', '👋', '✨']):
                answer += " 😊"
            
            return answer

        except Exception as e:
            print(f"   ⚠️ Conversational error: {e}")
            # Enhanced fallback responses
            if 'terima' in user_message.lower():
                return "Sama-sama! 😊 Saya sedia membantu bila-bila masa. Ada soalan lain? 💙"
            elif any(word in user_message.lower() for word in ['hai', 'hello', 'assalam']):
                return "Waalaikumussalam! 😊 Saya ZAKIA dari LZNK Kedah. Ada apa yang boleh saya bantu hari ni? 💙"
            else:
                return "Terima kasih! Saya di sini untuk bantu anda 😊 Ada soalan tentang zakat? 💙"

    def test_connection(self):
        """Enhanced connection test"""
        try:
            test_prompts = [
                "Kata 'Berfungsi' dalam Bahasa Melayu",
                "Berapa 2+2?",
                "Apa itu zakat?"
            ]
            
            results = []
            for prompt in test_prompts:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=50,
                    )
                )
                results.append(response.text.strip())
            
            return {
                "success": True,
                "model": self.model_name,
                "test_results": results,
                "message": f"✅ Gemini {self.model_name} - ENHANCED MODE Ready!"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "❌ Connection test failed!"
            }


# Quick test function
def test_enhanced_service():
    """Test the enhanced service"""
    try:
        print("🧪 Testing Enhanced Gemini Service...\n")
        
        service = GeminiService()
        
        # Test 1: Connection
        print("1️⃣ Testing connection...")
        result = service.test_connection()
        print(f"   {result['message']}\n")
        
        # Test 2: FAQ Enhancement
        print("2️⃣ Testing FAQ enhancement...")
        test_faq = "Nisab zakat pendapatan RM15,000 setahun, kadar 2.5%"
        enhanced = service.enhance_faq_response(
            "Berapa nisab zakat pendapatan?",
            test_faq
        )
        print(f"   Original: {test_faq}")
        print(f"   Enhanced: {enhanced}\n")
        
        # Test 3: Smart Answer
        print("3️⃣ Testing smart answer...")
        answer = service.answer_zakat_question("Apa itu haul dalam zakat?")
        print(f"   Answer: {answer}\n")
        
        # Test 4: Conversational
        print("4️⃣ Testing conversational...")
        conv = service.generate_conversational_response("Terima kasih banyak!")
        print(f"   Response: {conv}\n")
        
        print("✅ All tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    test_enhanced_service()