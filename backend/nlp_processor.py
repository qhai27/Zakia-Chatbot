"""
Backend NLP processor with FAQ training, keyword extraction, similarity scoring,
"""

import re
import json
from difflib import SequenceMatcher
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict
import unicodedata

# Try optional import of GeminiService (non-fatal if missing)
try:
    from gemini_service import GeminiService
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False
    GeminiService = None  # type: ignore

class NLPProcessor:
    def __init__(self, enable_gemini: bool = True):
        # Training data storage
        self.training_pairs: List[Dict] = []
        self.keyword_index: Dict[str, List[int]] = {}
        
        # Conversation context
        self.conversation_history = defaultdict(list)
        self.context_keywords = defaultdict(dict)
        
        # Stopwords (Malay + English)
        self.stopwords = {
            'yang', 'dan', 'atau', 'dengan', 'untuk', 'dari', 'ke', 'di', 'pada',
            'adalah', 'ialah', 'ini', 'itu', 'saya', 'anda', 'kami', 'mereka',
            'akan', 'telah', 'sudah', 'boleh', 'dapat', 'ada', 'mana', 'bila',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        }
        
        # Typo corrections
        self.typo_corrections = {
            'zakat': ['zakat', 'zakah', 'zakt', 'zkat', 'zaket'],
            'bayar': ['bayar', 'bayr', 'byr', 'membayar', 'pembayaran', 'pay', 'payment'],
            'bagaimana': ['bagaimana', 'bgaimana', 'bgmn', 'bagaimanakah', 'mcm mana', 'macam mana', 'how'],
            'apa': ['apa', 'ap', 'apakah', 'pe', 'what', 'maksud'],
            'siapa': ['siapa', 'sipa', 'siapakah', 'sape', 'who'],
            'berapa': ['berapa', 'brp', 'brpa', 'berapakah', 'brape', 'how much', 'how many'],
            'bila': ['bila', 'bl', 'bilakah', 'bile', 'when'],
            'mana': ['mana', 'mn', 'manakah', 'mne', 'where'],
            'kenapa': ['kenapa', 'knp', 'kenapakah', 'nape', 'why','mengapa'],
            'lznk': ['lznk', 'lembaga zakat', 'lembaga zakat negeri kedah', 'lembaga'],
            'nisab': ['nisab', 'threshold'],
            'fitrah': ['fitrah', 'fitr'],
            'emas': ['emas', 'gold'],
            'wang': ['wang', 'duit', 'money', 'cash'],
            'pejabat': ['pejabat', 'office', 'kaunter', 'cawangan', 'branch'],
            'bantuan': ['bantuan', 'help', 'tolong', 'assist', 'aid'],
            'mohon': ['mohon', 'apply', 'permohonan', 'application'],
            'syarat': ['syarat', 'syrt', 'syart'],
            'khairiat': ['khairiat', 'khairat', 'khairiat', 'kheiriyat'],
            'saya': ['saya', 'sy', 'aku', 'i', 'me'],
            'anda': ['anda', 'akau', 'you', 'u'],
            'kami': ['kami', 'kmi', 'we', 'us'],
            'mereka': ['mereka', 'mrk', 'they', 'them'],
        }
        
        # Synonyms
        self.synonyms = {
            'cara': ['cara', 'kaedah', 'method', 'bagaimana', 'how', 'steps','cara-cara'],
            'lokasi': ['lokasi', 'tempat', 'alamat', 'mana', 'location', 'address', 'where'],
            'waktu': ['waktu', 'masa', 'tempoh', 'bila', 'time', 'when', 'period'],
            'jumlah': ['jumlah', 'berapa', 'nilai', 'kadar', 'amount', 'rate'],
            'wajib': ['wajib', 'mesti', 'perlu', 'kena', 'must', 'required', 'mandatory'],
            'bayar': ['bayar', 'membayar', 'pembayaran', 'selesai', 'pay', 'payment'],
            'bantuan': ['bantuan', 'help', 'tolong', 'assist', 'aid', 'support'],
            'pejabat': ['pejabat', 'office', 'kaunter', 'cawangan', 'branch'],
            'mohon': ['mohon', 'apply', 'permohonan', 'application', 'request'],
            'kena': ['kena', 'perlu', 'wajib', 'mesti', 'need to', 'must'],
            'menerima': ['menerima', 'terima', 'dapat', 'receive', 'get', 'obtain'],
            'sehingga': ['sehingga', 'sampai', 'hingga', 'until', 'up to', 'till'],
            'segera' :['cepat', 'pantas', 'laju', 'urgent', 'immediately', 'asap'],
            'informasi': ['info', 'maklumat', 'information', 'details', 'data'],
            'muallaf':['mualaf','new convert','new muslim','convert', 'convert to islam', 'newly converted','baru convert'],
            'pembelajaran':['belajar','study','learning','education','pendidikan'],
            'polisi':['policy','peraturan','rules','guidelines','garis panduan'],
            'insurans':['insurance','takaful','coverage','protection','insurans', 'insurans takaful','insuran'],
            'isteri': ['isteri', 'wife', 'spouse', 'pasangan', 'ibu'],
            'pinjam': ['pinjaman', 'loan', 'borrow', 'hutang', 'debt'],
            'menampung' : ['tampung','support','sokong','cover','sara'],
            'Fixed Deposit' : ['fixed deposit','fd','deposit tetap','simpanan tetap','fixed deposit account'],
            'pinjaman' : ['loan','pinjam','hutang','debt','borrow'],
            'setahun' : ['setahun','1 tahun','one year','1 year','setahun sekali','once a year' ,'annually', 'satu tahun'],
            'lewat' : ['lewat','terlewat','late','overdue','delay','terlambat','melewatkan', 'menunda', 'melewatkan'],
            'faqir': ['fakir', 'poor', 'needy', 'destitute'],
            'bapa': ['bapa', 'ayah', 'father', 'dad', 'parent'],
            'saya mempunyai': ['saya ada', 'saya punya' 'i have', 'i own', 'i possess', 'i got'],
            'khairiat kematian': ['khairat', 'khairiat', 'funeral fund', 'funeral assistance'],
            'perbezaan': ['perbezaan', 'bezanya', 'difference', 'distinction', 'variety', 'beza'],
            'apakah' : ['apakah','apa itu','what is','define','meaning of', 'apa itu', 'maksud'],
            'apa itu' : ['apa itu','apakah','what is','define','meaning of', 'maksud'],
        }
        
        # Optional Gemini integration
        self.gemini = None
        if enable_gemini and GEMINI_AVAILABLE:
            try:
                self.gemini = GeminiService()
                print("✅ GeminiService loaded inside NLPProcessor")
            except Exception as e:
                print("⚠️ GeminiService initialization failed:", e)
                self.gemini = None
        else:
            if enable_gemini:
                print("⚠️ GeminiService not available — running without Gemini.")
        
        print("✅ NLP Processor initialized")
    
    # ----------------------------
    # Utilities
    # ----------------------------
    def _normalize_unicode(self, text: str) -> str:
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in nfkd if not unicodedata.combining(c)])
    
    # ----------------------------
    # Training
    # ----------------------------
    def train_from_faqs(self, faqs: List[Dict]) -> bool:
        print(f"🎓 Training NLP with {len(faqs)} FAQs...")
        
        self.training_pairs = []
        self.keyword_index = {}
        
        if not faqs:
            print("⚠️ No FAQs provided for training")
            return False
        
        for faq in faqs:
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            category = faq.get('category', 'Umum')
            
            if not question or not answer:
                continue
            
            keywords = self.extract_keywords(question)
            
            self.training_pairs.append({
                'question': question,
                'answer': answer,
                'category': category,
                'keywords': keywords
            })
            
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append(len(self.training_pairs) - 1)
        
        print(f"✅ Training complete! Pairs: {len(self.training_pairs)}, Unique keywords: {len(self.keyword_index)}")
        return True
    
    # ----------------------------
    # Keyword extraction
    # ----------------------------
    def extract_keywords(self, text: str) -> List[str]:
        if not text:
            return []
        
        text = self._normalize_unicode(text)
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        words = text.split()
        
        corrected_words = []
        for word in words:
            corrected = word
            for correct, variants in self.typo_corrections.items():
                if word in variants:
                    corrected = correct
                    break
            corrected_words.append(corrected)
        
        keywords = [w for w in corrected_words if w not in self.stopwords and len(w) > 2]
        
        bigrams = []
        for i in range(len(keywords) - 1):
            bigram = f"{keywords[i]} {keywords[i+1]}"
            bigrams.append(bigram)
        
        expanded = set(keywords + bigrams)
        for kw in list(expanded):
            if kw in self.synonyms:
                expanded.update(self.synonyms[kw])
        
        return list(expanded)
    
    # ----------------------------
    # Preprocessing & similarity
    # ----------------------------
    def preprocess_text(self, text: str) -> str:
        if not text:
            return ""
        text = self._normalize_unicode(text)
        text = text.lower().strip()
        text = re.sub(r'[^\w\s\?]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def calculate_similarity(self, text1: str, text2: str, context_boost: float = 0.0) -> float:
        t1 = self.preprocess_text(text1)
        t2 = self.preprocess_text(text2)
        
        sequence_sim = SequenceMatcher(None, t1, t2).ratio() * 0.4
        
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        if keywords1 and keywords2:
            intersection = len(keywords1.intersection(keywords2))
            union = len(keywords1.union(keywords2))
            keyword_sim = (intersection / union) * 0.45 if union > 0 else 0
        else:
            keyword_sim = 0
        
        words1 = set(t1.split())
        words2 = set(t2.split())
        if words1 and words2:
            word_intersection = len(words1.intersection(words2))
            word_union = len(words1.union(words2))
            word_sim = (word_intersection / word_union) * 0.15 if word_union > 0 else 0
        else:
            word_sim = 0
        
        final_score = sequence_sim + keyword_sim + word_sim + context_boost
        return min(final_score, 1.0)
    
    # ----------------------------
    # Matching & response
    # ----------------------------
    def find_best_match(self, user_input: str, faqs: List[Dict], session_id: str = None) -> Tuple[Dict, float]:
        if not faqs:
            return None, 0.0
        
        context_boost_map = {}
        if session_id and session_id in self.context_keywords:
            context_keywords = set(self.context_keywords[session_id].keys())
            for idx, faq in enumerate(faqs):
                faq_keywords = set(self.extract_keywords(faq.get('question', '')))
                context_overlap = len(faq_keywords.intersection(context_keywords))
                if context_overlap > 0:
                    context_boost_map[idx] = min(context_overlap * 0.05, 0.15)
        
        best_match = None
        best_score = 0.0
        
        candidates = []
        user_keywords = self.extract_keywords(user_input)
        if self.keyword_index and user_keywords:
            for keyword in user_keywords:
                if keyword in self.keyword_index:
                    candidates.extend(self.keyword_index[keyword])
            candidates = list(set(candidates))
        
        if not candidates:
            candidates = list(range(len(faqs)))
        
        for idx in candidates:
            if idx >= len(faqs):
                continue
            faq = faqs[idx]
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            context_boost = context_boost_map.get(idx, 0.0)
            q_score = self.calculate_similarity(user_input, question, context_boost)
            a_score = self.calculate_similarity(user_input, answer, context_boost * 0.5) * 0.3
            user_kw_set = set(user_keywords)
            faq_kw_set = set(self.extract_keywords(question))
            exact_matches = len(user_kw_set.intersection(faq_kw_set))
            keyword_boost = min(exact_matches * 0.1, 0.25)
            total_score = q_score + a_score + keyword_boost
            if total_score > best_score:
                best_score = total_score
                best_match = faq
        
        return best_match, best_score
    
    def generate_response(self, user_input: str, faqs: List[Dict], 
                         session_id: str = None, threshold: float = 0.35) -> Dict:
        if session_id:
            self.add_to_context(session_id, user_input, 'user')
        
        best_match, score = self.find_best_match(user_input, faqs, session_id)
        
        # If good match, possibly enhance with Gemini
        if best_match and score >= threshold:
            if score >= 0.75:
                confidence_level = "high"
            elif score >= 0.55:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            reply_text = best_match['answer']
            use_gemini_flag = (score < 0.65) and (self.gemini is not None)
            
            # If gemini available and flagged, try to enhance answer (non-fatal)
            if use_gemini_flag:
                try:
                    enhanced = self.gemini.enhance_faq_response(user_question=user_input, faq_answer=reply_text)
                    # Basic safety: only use enhanced if it's not empty and longer than small threshold
                    if enhanced and len(enhanced) > 20:
                        reply_text = enhanced
                except Exception as e:
                    # Log error and fall back to FAQ answer
                    print("⚠️ Gemini enhancement failed:", e)
            
            response = {
                'reply': reply_text,
                'matched_question': best_match['question'],
                'confidence': float(score),
                'confidence_level': confidence_level,
                'category': best_match.get('category', 'Umum'),
                'use_gemini': use_gemini_flag,
                'matched': True
            }
            
            if session_id:
                self.add_to_context(session_id, response['reply'], 'bot')
            return response
        
        # No good match -> fallback (use Gemini to craft helpful reply if available)
        similar_questions = self._get_similar_questions(user_input, faqs, top_n=3)
        reply_text = None
        if self.gemini:
            try:
                reply_text = self.gemini.generate_fallback_response(user_question=user_input, matched_questions=similar_questions)
            except Exception as e:
                print("⚠️ Gemini fallback failed:", e)
                reply_text = None
        
        if not reply_text:
            reply_text = self._generate_fallback(similar_questions)
        
        response = {
            'reply': reply_text,
            'matched_question': None,
            'confidence': float(score),
            'confidence_level': 'none',
            'category': 'Umum',
            'use_gemini': bool(self.gemini),
            'matched': False,
            'similar_questions': similar_questions
        }
        
        if session_id:
            self.add_to_context(session_id, response['reply'], 'bot')
        return response
    
    # ----------------------------
    # Helpers for suggestions & fallback
    # ----------------------------
    def _get_similar_questions(self, user_input: str, faqs: List[Dict], top_n: int = 3) -> List[str]:
        scored_questions = []
        for faq in faqs:
            question = faq.get('question', '')
            score = self.calculate_similarity(user_input, question)
            scored_questions.append((question, score))
        scored_questions.sort(key=lambda x: x[1], reverse=True)
        return [q for q, s in scored_questions[:top_n] if s > 0.2]
    
    def _generate_fallback(self, similar_questions: List[str] = None) -> str:
        fallback = "Maaf, saya kurang faham soalan anda.\n\n"
        if similar_questions and len(similar_questions) > 0:
            fallback += "Mungkin anda ingin tanya tentang:\n"
            for i, q in enumerate(similar_questions, 1):
                fallback += f"{i}. {q}\n"
            fallback += "\n"
        fallback += ("Anda juga boleh bertanya tentang:\n"
                    "• Cara membayar zakat\n"
                    "• Pengiraan zakat pendapatan/simpanan\n"
                    "• Maklumat nisab dan kadar zakat\n"
                    "• Lokasi dan perkhidmatan LZNK")
        return fallback
    
    # ----------------------------
    # Conversation context
    # ----------------------------
    def add_to_context(self, session_id: str, message: str, role: str):
        self.conversation_history[session_id].append({
            'role': role,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'keywords': self.extract_keywords(message) if role == 'user' else []
        })
        if len(self.conversation_history[session_id]) > 15:
            self.conversation_history[session_id] = self.conversation_history[session_id][-15:]
        if role == 'user':
            keywords = self.extract_keywords(message)
            for keyword in keywords:
                if keyword not in self.context_keywords[session_id]:
                    self.context_keywords[session_id][keyword] = 1
                else:
                    self.context_keywords[session_id][keyword] += 1
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        return self.conversation_history.get(session_id, [])
    
    def clear_session_context(self, session_id: str):
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
        if session_id in self.context_keywords:
            del self.context_keywords[session_id]
    
    # ----------------------------
    # Intent detection
    # ----------------------------
    def analyze_user_intent(self, user_input: str) -> Dict:
        text = self.preprocess_text(user_input)
        question_words = ['apa', 'siapa', 'bagaimana', 'bila', 'mana', 'kenapa', 'berapa',
                         'what', 'who', 'how', 'when', 'where', 'why', 'can', 'could']
        greeting_words = ['hai', 'hello', 'hi', 'assalam', 'salam', 'selamat', 'good morning', 
                         'good afternoon', 'good evening']
        thanks_words = ['terima kasih', 'thanks', 'tq', 'thank you', 'grateful', 'appreciate']
        goodbye_words = ['bye', 'selamat tinggal', 'jumpa lagi', 'goodbye', 'see you', 'farewell']
        intent = {
            'is_question': '?' in user_input or any(word in text for word in question_words),
            'is_greeting': any(word in text for word in greeting_words),
            'is_thanks': any(word in text for word in thanks_words),
            'is_goodbye': any(word in text for word in goodbye_words),
            'keywords': self.extract_keywords(user_input),
            'language': self._detect_language(text)
        }
        return intent
    
    def _detect_language(self, text: str) -> str:
        malay_indicators = ['apa', 'siapa', 'bagaimana', 'bila', 'mana', 'kenapa', 'berapa',
                           'zakat', 'bayar', 'terima kasih', 'assalam']
        english_indicators = ['what', 'who', 'how', 'when', 'where', 'why', 'can',
                             'thank you', 'hello', 'please']
        malay_count = sum(1 for word in malay_indicators if word in text)
        english_count = sum(1 for word in english_indicators if word in text)
        if malay_count > english_count:
            return 'malay'
        elif english_count > malay_count:
            return 'english'
        else:
            return 'mixed'
    
    # ----------------------------
    # Save / Load training
    # ----------------------------
    def save_training_data(self, filename: str = 'training_data.json') -> bool:
        try:
            data = {
                'training_pairs': self.training_pairs,
                'keyword_index': self.keyword_index,
                'timestamp': datetime.now().isoformat(),
                'total_pairs': len(self.training_pairs),
                'total_keywords': len(self.keyword_index)
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Training data saved to {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving training data: {e}")
            return False
    
    def load_training_data(self, filename: str = 'training_data.json') -> bool:
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
        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            return False
    
    def get_stats(self) -> Dict:
        return {
            'training_pairs': len(self.training_pairs),
            'unique_keywords': len(self.keyword_index),
            'active_sessions': len(self.conversation_history),
            'total_context_keywords': sum(len(k) for k in self.context_keywords.values())
        }
