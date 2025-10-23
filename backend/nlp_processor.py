import re
import difflib
from typing import List, Tuple, Dict
import json
from datetime import datetime

class NLPProcessor:
    def __init__(self):
        # Malay stopwords for better filtering
        self.stopwords = {
            'yang', 'dan', 'atau', 'dengan', 'untuk', 'dari', 'ke', 'di', 'pada',
            'adalah', 'ialah', 'ini', 'itu', 'saya', 'anda', 'kami', 'mereka',
            'akan', 'telah', 'sudah', 'boleh', 'dapat', 'ada', 'mana', 'bila'
        }
        
        # Enhanced typo corrections
        self.typo_corrections = {
            'zakat': ['zakat', 'zakah', 'zakt', 'zkat'],
            'bayar': ['bayar', 'bayr', 'byr', 'membayar', 'pembayaran'],
            'bagaimana': ['bagaimana', 'bgaimana', 'bgmn', 'bagaimanakah', 'mcm mana', 'macam mana'],
            'apa': ['apa', 'ap', 'apakah', 'pe'],
            'siapa': ['siapa', 'sipa', 'siapakah', 'sape'],
            'berapa': ['berapa', 'brp', 'brpa', 'berapakah', 'brape'],
            'bila': ['bila', 'bl', 'bilakah', 'bile'],
            'mana': ['mana', 'mn', 'manakah', 'mne'],
            'kenapa': ['kenapa', 'knp', 'kenapakah', 'nape'],
            'mengapa': ['mengapa', 'mngp', 'mengapakah', 'ngape'],
            'lznk': ['lznk', 'lznk', 'lembaga zakat'],
            'nisab': ['nisab', 'nisab', 'nisab'],
            'haul': ['haul', 'haul', 'haul'],
            'fitrah': ['fitrah', 'fitrah', 'fitrah'],
            'emas': ['emas', 'emas', 'gold'],
            'wang': ['wang', 'duit', 'money']
        }
        
        # Synonym expansion for better matching
        self.synonyms = {
            'cara': ['cara', 'kaedah', 'method', 'bagaimana'],
            'lokasi': ['lokasi', 'tempat', 'alamat', 'mana'],
            'waktu': ['waktu', 'masa', 'tempoh', 'bila'],
            'jumlah': ['jumlah', 'berapa', 'nilai', 'kadar'],
            'wajib': ['wajib', 'mesti', 'perlu', 'kena'],
            'bayar': ['bayar', 'membayar', 'pembayaran', 'selesai'],
            'bantuan': ['bantuan', 'help', 'tolong', 'assist'],
            'pejabat': ['pejabat', 'office', 'kaunter', 'cawangan']
        }
        
        # Question word mappings
        self.question_words = {
            'what': ['apa', 'apakah'],
            'who': ['siapa', 'siapakah'],
            'how': ['bagaimana', 'bgmn', 'macam mana'],
            'when': ['bila', 'bilakah'],
            'where': ['mana', 'di mana', 'manakah'],
            'why': ['kenapa', 'mengapa'],
            'how_much': ['berapa', 'berapakah']
        }
        
        # Training data storage
        self.training_pairs = []
        self.keyword_index = {}
        
    def preprocess_text(self, text: str) -> str:
        """Enhanced text preprocessing"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation except question marks
        text = re.sub(r'[^\w\s?]', '', text)
        
        # Fix common typos
        words = text.split()
        corrected_words = []
        
        for word in words:
            corrected = word
            for correct, variants in self.typo_corrections.items():
                if word in variants:
                    corrected = correct
                    break
            corrected_words.append(corrected)
        
        return ' '.join(corrected_words)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords"""
        text = self.preprocess_text(text)
        words = text.split()
        
        # Remove stopwords and short words
        keywords = [
            word for word in words 
            if word not in self.stopwords and len(word) > 2
        ]
        
        # Add synonym variations
        expanded_keywords = set(keywords)
        for keyword in keywords:
            if keyword in self.synonyms:
                expanded_keywords.update(self.synonyms[keyword])
        
        return list(expanded_keywords)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity with multiple methods"""
        # Method 1: Sequence matching
        t1 = self.preprocess_text(text1)
        t2 = self.preprocess_text(text2)
        sequence_sim = difflib.SequenceMatcher(None, t1, t2).ratio()
        
        # Method 2: Keyword overlap
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if keywords1 and keywords2:
            intersection = len(keywords1.intersection(keywords2))
            union = len(keywords1.union(keywords2))
            keyword_sim = intersection / union if union > 0 else 0
        else:
            keyword_sim = 0
        
        # Method 3: Word-level similarity
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        if words1 and words2:
            word_intersection = len(words1.intersection(words2))
            word_union = len(words1.union(words2))
            word_sim = word_intersection / word_union if word_union > 0 else 0
        else:
            word_sim = 0
        
        # Weighted combination
        final_score = (
            sequence_sim * 0.3 +
            keyword_sim * 0.5 +
            word_sim * 0.2
        )
        
        return final_score
    
    def train_from_faqs(self, faqs: List[Dict]):
        """Train the model from FAQ data"""
        print(f"Training with {len(faqs)} FAQs...")
        
        self.training_pairs = []
        self.keyword_index = {}
        
        for faq in faqs:
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            category = faq.get('category', 'Umum')
            
            if not question or not answer:
                continue
            
            # Store training pair
            self.training_pairs.append({
                'question': question,
                'answer': answer,
                'category': category,
                'keywords': self.extract_keywords(question)
            })
            
            # Build keyword index
            for keyword in self.extract_keywords(question):
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(len(self.training_pairs) - 1)
        
        print(f"✅ Training complete! Indexed {len(self.keyword_index)} unique keywords")
    
    def find_best_match(self, user_input: str, faqs: List[Dict]) -> Tuple[Dict, float]:
        """Find best match using trained data and multiple strategies"""
        if not faqs:
            return None, 0.0
        
        user_keywords = set(self.extract_keywords(user_input))
        candidates = []
        
        # Strategy 1: Keyword-based filtering
        for keyword in user_keywords:
            if keyword in self.keyword_index:
                for idx in self.keyword_index[keyword]:
                    if idx < len(self.training_pairs):
                        candidates.append(idx)
        
        # If no candidates from keywords, use all FAQs
        if not candidates:
            candidates = list(range(len(faqs)))
        else:
            # Remove duplicates and sort by frequency
            candidates = sorted(set(candidates), 
                              key=lambda x: candidates.count(x), 
                              reverse=True)
        
        # Strategy 2: Calculate similarity for candidates
        best_match = None
        best_score = 0.0
        
        for idx in candidates[:20]:  # Check top 20 candidates
            if idx >= len(faqs):
                continue
                
            faq = faqs[idx]
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            
            # Calculate similarities
            q_sim = self.calculate_similarity(user_input, question)
            a_sim = self.calculate_similarity(user_input, answer) * 0.3
            
            # Boost for exact keyword matches
            faq_keywords = set(self.extract_keywords(question))
            exact_matches = len(user_keywords.intersection(faq_keywords))
            keyword_boost = min(exact_matches * 0.15, 0.3)
            
            total_score = q_sim + a_sim + keyword_boost
            
            if total_score > best_score:
                best_score = total_score
                best_match = faq
        
        return best_match, best_score
    
    def generate_response(self, user_input: str, faqs: List[Dict], threshold: float = 0.35) -> Dict:
        """Generate response with confidence scoring"""
        best_match, score = self.find_best_match(user_input, faqs)
        
        if best_match and score >= threshold:
            confidence_level = "high" if score >= 0.7 else "medium" if score >= 0.5 else "low"
            
            return {
                'reply': best_match['answer'],
                'matched_question': best_match['question'],
                'confidence': score,
                'confidence_level': confidence_level,
                'category': best_match.get('category', 'Umum')
            }
        else:
            # Generate contextual fallback
            intent = self.analyze_user_intent(user_input)
            fallback = self.get_contextual_fallback(user_input, intent, faqs)
            
            return {
                'reply': fallback,
                'matched_question': None,
                'confidence': score,
                'confidence_level': 'none',
                'category': intent.get('category', 'Unknown')
            }
    
    def analyze_user_intent(self, user_input: str) -> Dict:
        """Analyze user intent"""
        text = self.preprocess_text(user_input)
        
        return {
            'is_question': '?' in user_input or any(
                word in text for qwords in self.question_words.values() 
                for word in qwords
            ),
            'is_greeting': any(word in text for word in [
                'assalamualaikum', 'salam', 'hello', 'hi', 'hai'
            ]),
            'is_thanks': any(word in text for word in [
                'terima kasih', 'thanks', 'tq'
            ]),
            'is_goodbye': any(word in text for word in [
                'bye', 'selamat tinggal', 'jumpa lagi'
            ]),
            'keywords': self.extract_keywords(user_input),
            'category': self.detect_category(text)
        }
    
    def get_contextual_fallback(self, user_input: str, intent: Dict, faqs: List[Dict]) -> str:
        """Generate helpful fallback responses"""
        category = intent.get('category', 'Unknown')
        
        fallback_templates = {
            'LZNK': "Maaf, saya tidak pasti tentang soalan LZNK tersebut. 😔 Anda boleh bertanya tentang perkhidmatan LZNK, lokasi pejabat, atau program bantuan.",
            'Pembayaran': "Maaf, saya tidak dapat membantu dengan soalan pembayaran tersebut. 💳 Anda boleh bertanya tentang cara membayar zakat atau kaedah pembayaran.",
            'Nisab': "Maaf, saya tidak pasti tentang soalan nisab tersebut. 📊 Anda boleh bertanya tentang nisab emas, perak, atau kadar zakat.",
        }
        
        if category in fallback_templates:
            return fallback_templates[category]
        
        # Get suggested questions
        suggestions = self.get_suggested_questions(faqs, intent['keywords'])
        if suggestions:
            return f"Maaf, saya tidak pasti tentang soalan tersebut. 🤔 Cuba tanya: {suggestions[0]}"
        
        return "Maaf, saya tidak dapat memahami soalan anda. 😔 Bolehkah anda cuba soalan lain tentang zakat atau LZNK?"
    
    def get_suggested_questions(self, faqs: List[Dict], keywords: List[str]) -> List[str]:
        """Get relevant question suggestions"""
        suggestions = []
        
        for faq in faqs:
            question = faq.get('question', '')
            for keyword in keywords:
                if keyword in question.lower():
                    suggestions.append(question)
                    break
        
        return suggestions[:3]
    
    def detect_category(self, text: str) -> str:
        """Detect question category"""
        category_keywords = {
            'LZNK': ['lznk', 'lembaga', 'kedah', 'pejabat', 'lokasi'],
            'Pembayaran': ['bayar', 'pembayaran', 'cara', 'kaedah'],
            'Nisab': ['nisab', 'nilai', 'kadar', 'jumlah'],
            'Perniagaan': ['perniagaan', 'niaga', 'bisnes'],
            'Haul': ['haul', 'tahun', 'tempoh']
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in text for kw in keywords):
                return category
        
        return 'Umum'
    
    def save_training_data(self, filename: str = 'training_data.json'):
        """Save trained data to file"""
        data = {
            'training_pairs': self.training_pairs,
            'keyword_index': self.keyword_index,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Training data saved to {filename}")
    
    def load_training_data(self, filename: str = 'training_data.json'):
        """Load trained data from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.training_pairs = data.get('training_pairs', [])
            self.keyword_index = data.get('keyword_index', {})
            
            print(f"✅ Training data loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"⚠️ Training file not found: {filename}")
            return False