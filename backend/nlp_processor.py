import re
import difflib
from typing import List, Tuple, Dict
import string
import re

class NLPProcessor:
    def __init__(self):
        # Common Malay typos and variations
        self.typo_corrections = {
            'zakat': ['zakat', 'zakah', 'zakat', 'zakat', 'zakat'],
            'bayar': ['bayar', 'bayar', 'bayr', 'byr', 'bayar'],
            'bagaimana': ['bagaimana', 'bgaimana', 'bgmn', 'bagaimana', 'bagaimana'],
            'apa': ['apa', 'ap', 'apa', 'apa', 'apa'],
            'siapa': ['siapa', 'sipa', 'siapa', 'siapa', 'siapa'],
            'berapa': ['berapa', 'brp', 'brpa', 'berapa', 'berapa'],
            'bila': ['bila', 'bl', 'bila', 'bila', 'bila'],
            'mana': ['mana', 'mn', 'mana', 'mana', 'mana'],
            'kenapa': ['kenapa', 'knp', 'kenapa', 'kenapa', 'kenapa'],
            'mengapa': ['mengapa', 'mngp', 'mengapa', 'mengapa', 'mengapa'],
            'lznk': ['lznk', 'lznk', 'lznk', 'lznk', 'lznk'],
            'lembaga': ['lembaga', 'lembaga', 'lembaga', 'lembaga', 'lembaga'],
            'kedah': ['kedah', 'kedah', 'kedah', 'kedah', 'kedah'],
            'emas': ['emas', 'emas', 'emas', 'emas', 'emas'],
            'perniagaan': ['perniagaan', 'perniagaan', 'perniagaan', 'perniagaan', 'perniagaan'],
            'pendapatan': ['pendapatan', 'pendapatan', 'pendapatan', 'pendapatan', 'pendapatan'],
            'fitrah': ['fitrah', 'fitrah', 'fitrah', 'fitrah', 'fitrah'],
            'haul': ['haul', 'haul', 'haul', 'haul', 'haul'],
            'nisab': ['nisab', 'nisab', 'nisab', 'nisab', 'nisab'],
            'asnaf': ['asnaf', 'asnaf', 'asnaf', 'asnaf', 'asnaf']
        }
        
        # Question patterns for better matching
        self.question_patterns = {
            'what': ['apa', 'apakah', 'ap', 'ap'],
            'who': ['siapa', 'sipa', 'siapa', 'siapa'],
            'how': ['bagaimana', 'bgaimana', 'bgmn', 'bagaimana'],
            'when': ['bila', 'bila', 'bl', 'bila'],
            'where': ['mana', 'mn', 'mana', 'mana'],
            'why': ['kenapa', 'mengapa', 'knp', 'mngp'],
            'how_much': ['berapa', 'brp', 'brpa', 'berapa']
        }
        
        # Synonyms for better matching
        self.synonyms = {
            'zakat': ['zakat', 'zakah', 'zakat', 'zakat'],
            'bayar': ['bayar', 'membayar', 'bayar', 'bayar'],
            'cara': ['cara', 'kaedah', 'metod', 'cara'],
            'waktu': ['waktu', 'masa', 'tempoh', 'waktu'],
            'lokasi': ['lokasi', 'tempat', 'alamat', 'lokasi'],
            'perkhidmatan': ['perkhidmatan', 'khidmat', 'servis', 'perkhidmatan'],
            'bantuan': ['bantuan', 'bantuan', 'bantuan', 'bantuan'],
            'program': ['program', 'program', 'program', 'program']
        }

    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation except question marks
        text = re.sub(r'[^\w\s?]', '', text)
        
        # Fix common typos
        for correct_word, variations in self.typo_corrections.items():
            for variation in variations:
                if variation in text:
                    text = text.replace(variation, correct_word)
        
        return text

    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        text = self.preprocess_text(text)
        
        # Split into words
        words = text.split()
        
        # Filter out common stop words
        stop_words = {'yang', 'dan', 'atau', 'dengan', 'untuk', 'dari', 'ke', 'di', 'pada', 'adalah', 'ialah', 'ini', 'itu', 'saya', 'anda', 'kami', 'mereka'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Preprocess both texts
        text1 = self.preprocess_text(text1)
        text2 = self.preprocess_text(text2)
        
        # Use difflib for sequence matching
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        # Boost similarity for keyword matches
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if keywords1 and keywords2:
            keyword_similarity = len(keywords1.intersection(keywords2)) / len(keywords1.union(keywords2))
            similarity = max(similarity, keyword_similarity * 0.8)
        
        return similarity

    def find_best_match(self, user_input: str, faqs: List[Dict]) -> Tuple[Dict, float]:
        """Find the best matching FAQ"""
        if not faqs:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for faq in faqs:
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            
            # Calculate similarity with question
            question_similarity = self.calculate_similarity(user_input, question)
            
            # Calculate similarity with answer (for cases where user asks about content)
            answer_similarity = self.calculate_similarity(user_input, answer)
            
            # Take the higher similarity
            similarity = max(question_similarity, answer_similarity)
            
            # Boost score for exact keyword matches
            user_keywords = set(self.extract_keywords(user_input))
            question_keywords = set(self.extract_keywords(question))
            
            if user_keywords and question_keywords:
                keyword_match = len(user_keywords.intersection(question_keywords)) / len(user_keywords)
                similarity = max(similarity, similarity + (keyword_match * 0.3))
            
            if similarity > best_score:
                best_score = similarity
                best_match = faq
        
        return best_match, best_score

    def generate_response(self, user_input: str, faqs: List[Dict], threshold: float = 0.3) -> Dict:
        """Generate appropriate response based on user input"""
        best_match, score = self.find_best_match(user_input, faqs)
        
        if best_match and score >= threshold:
            return {
                'reply': best_match['answer'],
                'matched_question': best_match['question'],
                'confidence': score,
                'category': best_match.get('category', 'Umum')
            }
        else:
            # Generate contextual fallback responses based on user intent
            intent = self.analyze_user_intent(user_input)
            fallback_response = self.get_contextual_fallback(user_input, intent, faqs)
            
            return {
                'reply': fallback_response,
                'matched_question': None,
                'confidence': 0.0,
                'category': intent.get('category', 'Unknown')
            }

    def analyze_user_intent(self, user_input: str) -> Dict:
        """Analyze user intent from input"""
        text = self.preprocess_text(user_input)
        
        intent = {
            'is_question': '?' in user_input or any(word in text for word in ['apa', 'siapa', 'bagaimana', 'bila', 'mana', 'kenapa', 'berapa', 'mengapa', 'apakah', 'bagaimanakah']),
            'is_greeting': any(word in text for word in ['assalamualaikum', 'salam', 'hello', 'hi', 'hai', 'selamat pagi', 'selamat petang', 'selamat malam']),
            'is_thanks': any(word in text for word in ['terima kasih', 'thanks', 'thank you', 'tq', 'terima kasih banyak', 'thanks banyak']),
            'is_goodbye': any(word in text for word in ['bye', 'selamat tinggal', 'goodbye', 'jumpa lagi', 'selamat jalan', 'see you']),
            'is_help_request': any(word in text for word in ['bantuan', 'help', 'tolong', 'boleh tolong', 'boleh bantu']),
            'is_complaint': any(word in text for word in ['masalah', 'problem', 'error', 'error', 'tidak berfungsi', 'rosak']),
            'is_praise': any(word in text for word in ['bagus', 'baik', 'terbaik', 'excellent', 'good', 'nice']),
            'is_confused': any(word in text for word in ['confused', 'keliru', 'tidak faham', 'tidak tahu', 'boleh jelaskan']),
            'keywords': self.extract_keywords(user_input),
            'category': self.detect_category(text),
            'sentiment': self.analyze_sentiment(text),
            'urgency': self.detect_urgency(text)
        }
        
        return intent

    def get_contextual_fallback(self, user_input: str, intent: Dict, faqs: List[Dict]) -> str:
        """Generate contextual fallback responses based on user intent"""
        text = self.preprocess_text(user_input)
        
        # Help request responses
        if intent['is_help_request']:
            return "Saya di sini untuk membantu! 😊 Anda boleh bertanya tentang zakat, LZNK, atau cara pembayaran. Apa yang ingin anda tahu?"
        
        # Complaint responses
        if intent['is_complaint']:
            return "Maaf atas masalah yang anda hadapi. 🙏 Saya akan cuba membantu. Bolehkah anda jelaskan masalah anda dengan lebih terperinci?"
        
        # Praise responses
        if intent['is_praise']:
            return "Terima kasih! 😊 Saya gembira dapat membantu. Adakah ada lagi yang ingin anda tanya tentang zakat atau LZNK?"
        
        # Confused responses
        if intent['is_confused']:
            return "Tidak mengapa, saya di sini untuk membantu! 😊 Bolehkah anda cuba bertanya dengan cara yang berbeza? Atau anda boleh bertanya tentang topik zakat yang lain."
        
        # Category-specific suggestions
        category = intent.get('category', 'Unknown')
        if category == 'LZNK':
            return "Maaf, saya tidak pasti tentang soalan LZNK tersebut. 😔 Anda boleh bertanya tentang perkhidmatan LZNK, lokasi pejabat, atau program bantuan yang ditawarkan."
        elif category == 'Pembayaran':
            return "Maaf, saya tidak dapat membantu dengan soalan pembayaran tersebut. 💳 Anda boleh bertanya tentang cara membayar zakat, kaedah pembayaran, atau waktu pembayaran."
        elif category == 'Nisab':
            return "Maaf, saya tidak pasti tentang soalan nisab tersebut. 📊 Anda boleh bertanya tentang nisab emas, perak, atau kadar zakat yang berbeza."
        elif category == 'Perniagaan':
            return "Maaf, saya tidak dapat membantu dengan soalan perniagaan tersebut. 🏢 Anda boleh bertanya tentang zakat perniagaan, cara mengira, atau syarat-syaratnya."
        elif category == 'Haul':
            return "Maaf, saya tidak pasti tentang soalan haul tersebut. ⏰ Anda boleh bertanya tentang tempoh haul, syarat haul, atau bila haul bermula."
        
        # General fallback with suggestions
        suggestions = self.get_suggested_questions(faqs, intent['keywords'])
        if suggestions:
            return f"Maaf, saya tidak pasti tentang soalan tersebut. 🤔 Bolehkah anda cuba soalan lain? Atau anda boleh bertanya tentang: {', '.join(suggestions[:3])}?"
        
        # Default fallback
        return "Maaf, saya tidak dapat memahami soalan anda. 😔 Saya hanya boleh membantu dengan soalan berkaitan zakat dan LZNK. Bolehkah anda cuba soalan lain?"
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of user input"""
        positive_words = ['bagus', 'baik', 'terbaik', 'excellent', 'good', 'nice', 'terima kasih', 'thanks']
        negative_words = ['buruk', 'tidak baik', 'masalah', 'problem', 'error', 'rosak', 'tidak berfungsi']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def detect_urgency(self, text: str) -> str:
        """Detect urgency level of user input"""
        urgent_words = ['segera', 'urgent', 'cepat', 'sekarang', 'bantuan', 'tolong', 'help']
        text_lower = text.lower()
        
        if any(word in text_lower for word in urgent_words):
            return 'high'
        elif '?' in text:
            return 'medium'
        else:
            return 'low'
    
    def get_suggested_questions(self, faqs: List[Dict], keywords: List[str]) -> List[str]:
        """Get suggested questions based on keywords"""
        suggestions = []
        
        if not keywords:
            return ["Apa itu zakat?", "Bagaimana cara membayar zakat?", "Apakah perkhidmatan LZNK?"]
        
        # Find FAQs that contain similar keywords
        for faq in faqs:
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            
            # Check if any keyword appears in question or answer
            for keyword in keywords:
                if keyword.lower() in question.lower() or keyword.lower() in answer.lower():
                    if question not in suggestions:
                        suggestions.append(question)
                        break
        
        # If no suggestions found, return default ones
        if not suggestions:
            suggestions = ["Apa itu zakat?", "Bagaimana cara membayar zakat?", "Apakah perkhidmatan LZNK?"]
        
        return suggestions[:5]  # Return top 5 suggestions

    def detect_category(self, text: str) -> str:
        """Detect the category of the question"""
        text = text.lower()
        
        if any(word in text for word in ['lznk', 'lembaga', 'kedah', 'pejabat', 'lokasi', 'alamat', 'cawangan']):
            return 'LZNK'
        elif any(word in text for word in ['bayar', 'pembayaran', 'cara bayar', 'kaedah', 'metod', 'bayar']):
            return 'Pembayaran'
        elif any(word in text for word in ['nisab', 'nilai', 'kadar', 'peratus', 'jumlah', 'nilai']):
            return 'Nisab'
        elif any(word in text for word in ['perniagaan', 'niaga', 'perdagangan', 'bisnes', 'business']):
            return 'Perniagaan'
        elif any(word in text for word in ['haul', 'tahun', 'tempoh', 'masa', 'waktu']):
            return 'Haul'
        elif any(word in text for word in ['emas', 'perak', 'simpanan', 'pendapatan', 'fitrah']):
            return 'Jenis Zakat'
        else:
            return 'Umum'
