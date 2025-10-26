import re
import difflib
from typing import List, Tuple, Dict
import json
from datetime import datetime
from collections import defaultdict

class NLPProcessor:
    def __init__(self):
        # Malay and English stopwords
        self.stopwords = {
            'yang', 'dan', 'atau', 'dengan', 'untuk', 'dari', 'ke', 'di', 'pada',
            'adalah', 'ialah', 'ini', 'itu', 'saya', 'anda', 'kami', 'mereka',
            'akan', 'telah', 'sudah', 'boleh', 'dapat', 'ada', 'mana', 'bila',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        }
        
        # Enhanced typo corrections for both languages
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
            'lznk': ['lznk', 'lembaga zakat', 'lembaga zakat negeri kedah'],
            'nisab': ['nisab', 'nisab', 'threshold'],
            'fitrah': ['fitrah', 'fitrah', 'fitr'],
            'emas': ['emas', 'gold'],
            'wang': ['wang', 'duit', 'money', 'cash'],
            'pejabat': ['pejabat', 'office', 'kaunter', 'cawangan', 'branch'],
            'bantuan': ['bantuan', 'help', 'tolong', 'assist', 'aid'],
            'mohon': ['mohon', 'apply', 'permohonan', 'application']
        }
        
        # Expanded synonyms
        self.synonyms = {
            'cara': ['cara', 'kaedah', 'method', 'bagaimana', 'how', 'steps'],
            'lokasi': ['lokasi', 'tempat', 'alamat', 'mana', 'location', 'address', 'where'],
            'waktu': ['waktu', 'masa', 'tempoh', 'bila', 'time', 'when', 'period'],
            'jumlah': ['jumlah', 'berapa', 'nilai', 'kadar', 'amount', 'rate'],
            'wajib': ['wajib', 'mesti', 'perlu', 'kena', 'must', 'required', 'mandatory'],
            'bayar': ['bayar', 'membayar', 'pembayaran', 'selesai', 'pay', 'payment'],
            'bantuan': ['bantuan', 'help', 'tolong', 'assist', 'aid', 'support'],
            'pejabat': ['pejabat', 'office', 'kaunter', 'cawangan', 'branch'],
            'mohon': ['mohon', 'apply', 'permohonan', 'application', 'request']
        }
        
        # Enhanced conversation context storage
        self.conversation_history = defaultdict(list)  # session_id -> [messages]
        self.context_keywords = defaultdict(dict)  # session_id -> {keyword: weight}
        self.conversation_topics = defaultdict(list)  # session_id -> [topics]
        self.user_preferences = defaultdict(dict)  # session_id -> {preference: value}
        self.conversation_entities = defaultdict(set)  # session_id -> {entities}
        
        # Training data
        self.training_pairs = []
        self.keyword_index = {}
        
    def preprocess_text(self, text: str) -> str:
        """Enhanced text preprocessing"""
        if not text:
            return ""
        
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s?]', '', text)
        
        # Fix typos
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
    
    def add_to_context(self, session_id: str, message: str, role: str):
        """Enhanced context management with better memory"""
        # Add message to conversation history
        self.conversation_history[session_id].append({
            'role': role,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'keywords': self.extract_keywords(message),
            'intent': self.analyze_user_intent(message) if role == 'user' else None,
            'category': self.detect_category(message) if role == 'user' else None
        })
        
        # Keep last 15 messages for better context
        if len(self.conversation_history[session_id]) > 15:
            self.conversation_history[session_id] = self.conversation_history[session_id][-15:]
        
        # Update context keywords with weighted importance
        message_keywords = self.extract_keywords(message)
        for keyword in message_keywords:
            if keyword not in self.context_keywords[session_id]:
                self.context_keywords[session_id][keyword] = 1
            else:
                self.context_keywords[session_id][keyword] += 1
        
        # Update conversation topics
        self._update_conversation_topics(session_id, message, role)
    
    def get_context_keywords(self, session_id: str) -> List[str]:
        """Get accumulated context keywords for a session with weights"""
        return list(self.context_keywords[session_id].keys())
    
    def get_weighted_context_keywords(self, session_id: str) -> Dict[str, int]:
        """Get context keywords with their importance weights"""
        return dict(self.context_keywords[session_id])
    
    def _update_conversation_topics(self, session_id: str, message: str, role: str):
        """Update conversation topics based on message content"""
        if role == 'user':
            # Extract topics from user message
            topics = self._extract_topics(message)
            for topic in topics:
                if topic not in self.conversation_topics[session_id]:
                    self.conversation_topics[session_id].append(topic)
            
            # Keep only last 5 topics
            if len(self.conversation_topics[session_id]) > 5:
                self.conversation_topics[session_id] = self.conversation_topics[session_id][-5:]
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract conversation topics from message"""
        topics = []
        text = self.preprocess_text(message)
        
        # Topic extraction patterns
        topic_patterns = {
            'zakat': ['zakat', 'zakah', 'zakat emas', 'zakat wang', 'zakat perniagaan'],
            'nisab': ['nisab', 'nilai', 'kadar', 'minimum'],
            'pembayaran': ['bayar', 'pembayaran', 'cara bayar', 'kaedah'],
            'lznk': ['lznk', 'lembaga', 'kedah', 'pejabat'],
            'bantuan': ['bantuan', 'help', 'assistance', 'mohon'],
            'asnaf': ['asnaf', 'penerima', 'layak', 'eligible']
        }
        
        for topic, keywords in topic_patterns.items():
            if any(keyword in text for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_conversation_summary(self, session_id: str) -> Dict:
        """Get a summary of the conversation context"""
        history = self.conversation_history[session_id]
        if not history:
            return {}
        
        return {
            'message_count': len(history),
            'topics': self.conversation_topics[session_id],
            'keywords': self.get_weighted_context_keywords(session_id),
            'last_user_message': history[-1]['message'] if history and history[-1]['role'] == 'user' else None,
            'conversation_duration': self._calculate_conversation_duration(history),
            'user_intents': [msg['intent'] for msg in history if msg.get('intent')],
            'categories_discussed': [msg['category'] for msg in history if msg.get('category')]
        }
    
    def _calculate_conversation_duration(self, history: List[Dict]) -> str:
        """Calculate how long the conversation has been going"""
        if len(history) < 2:
            return "Just started"
        
        first_time = datetime.fromisoformat(history[0]['timestamp'])
        last_time = datetime.fromisoformat(history[-1]['timestamp'])
        duration = last_time - first_time
        
        if duration.total_seconds() < 60:
            return f"{int(duration.total_seconds())} seconds"
        elif duration.total_seconds() < 3600:
            return f"{int(duration.total_seconds() / 60)} minutes"
        else:
            return f"{int(duration.total_seconds() / 3600)} hours"
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        return self.conversation_history[session_id]
    
    def detect_followup_question(self, user_input: str, session_id: str) -> bool:
        """Enhanced follow-up question detection with context awareness"""
        history = self.get_conversation_history(session_id)
        if len(history) < 2:
            return False
        
        text = self.preprocess_text(user_input)
        
        # Enhanced follow-up indicators
        followup_indicators = [
            'itu', 'ini', 'tersebut', 'that', 'this', 'it', 'there',
            'ada lagi', 'what about', 'how about', 'boleh tanya lagi',
            'one more thing', 'selain', 'other than', 'juga', 'also',
            'dan', 'and', 'atau', 'or', 'bagaimana pula', 'what about',
            'boleh', 'can', 'bolehkah', 'could', 'mungkin', 'maybe'
        ]
        
        # Check for pronouns and references
        has_indicators = any(indicator in text for indicator in followup_indicators)
        
        # Check for context continuity
        context_continuity = self._check_context_continuity(user_input, session_id)
        
        # Check for topic continuation
        topic_continuation = self._check_topic_continuation(user_input, session_id)
        
        return has_indicators or context_continuity or topic_continuation
    
    def _check_context_continuity(self, user_input: str, session_id: str) -> bool:
        """Check if the input continues the previous context"""
        history = self.get_conversation_history(session_id)
        if not history:
            return False
        
        # Get recent context keywords
        recent_keywords = set()
        for msg in history[-3:]:  # Last 3 messages
            if msg.get('keywords'):
                recent_keywords.update(msg['keywords'])
        
        # Check if current input shares keywords with recent context
        current_keywords = set(self.extract_keywords(user_input))
        shared_keywords = recent_keywords.intersection(current_keywords)
        
        return len(shared_keywords) > 0
    
    def _check_topic_continuation(self, user_input: str, session_id: str) -> bool:
        """Check if the input continues the current topic"""
        current_topics = self._extract_topics(user_input)
        conversation_topics = self.conversation_topics[session_id]
        
        # Check if current topics overlap with conversation topics
        return any(topic in conversation_topics for topic in current_topics)
    
    def calculate_similarity(self, text1: str, text2: str, context_boost: float = 0.0) -> float:
        """Calculate similarity with context boost"""
        t1 = self.preprocess_text(text1)
        t2 = self.preprocess_text(text2)
        
        # Sequence matching
        sequence_sim = difflib.SequenceMatcher(None, t1, t2).ratio()
        
        # Keyword overlap
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if keywords1 and keywords2:
            intersection = len(keywords1.intersection(keywords2))
            union = len(keywords1.union(keywords2))
            keyword_sim = intersection / union if union > 0 else 0
        else:
            keyword_sim = 0
        
        # Word-level similarity
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        if words1 and words2:
            word_intersection = len(words1.intersection(words2))
            word_union = len(words1.union(words2))
            word_sim = word_intersection / word_union if word_union > 0 else 0
        else:
            word_sim = 0
        
        # Weighted combination with context boost
        final_score = (
            sequence_sim * 0.3 +
            keyword_sim * 0.5 +
            word_sim * 0.2 +
            context_boost
        )
        
        return min(final_score, 1.0)
    
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
    
    def find_best_match(self, user_input: str, faqs: List[Dict], session_id: str = None) -> Tuple[Dict, float]:
        """Find best match with context awareness"""
        if not faqs:
            return None, 0.0
        
        user_keywords = set(self.extract_keywords(user_input))
        candidates = []
        
        # Get context keywords if session exists
        context_boost_map = {}
        if session_id:
            context_keywords = set(self.get_context_keywords(session_id))
            
            # Calculate context relevance for each FAQ
            for idx, pair in enumerate(self.training_pairs):
                faq_keywords = set(pair['keywords'])
                context_overlap = len(faq_keywords.intersection(context_keywords))
                if context_overlap > 0:
                    context_boost_map[idx] = min(context_overlap * 0.1, 0.2)
        
        # Strategy 1: Keyword-based filtering
        for keyword in user_keywords:
            if keyword in self.keyword_index:
                for idx in self.keyword_index[keyword]:
                    if idx < len(self.training_pairs):
                        candidates.append(idx)
        
        # If no candidates, use all FAQs
        if not candidates:
            candidates = list(range(len(faqs)))
        else:
            candidates = sorted(set(candidates), 
                              key=lambda x: candidates.count(x), 
                              reverse=True)
        
        # Strategy 2: Calculate similarity with context boost
        best_match = None
        best_score = 0.0
        
        for idx in candidates[:20]:
            if idx >= len(faqs):
                continue
                
            faq = faqs[idx]
            question = faq.get('question', '')
            answer = faq.get('answer', '')
            
            # Get context boost for this FAQ
            context_boost = context_boost_map.get(idx, 0.0)
            
            # Calculate similarities
            q_sim = self.calculate_similarity(user_input, question, context_boost)
            a_sim = self.calculate_similarity(user_input, answer, context_boost * 0.5) * 0.3
            
            # Boost for exact keyword matches
            faq_keywords = set(self.extract_keywords(question))
            exact_matches = len(user_keywords.intersection(faq_keywords))
            keyword_boost = min(exact_matches * 0.15, 0.3)
            
            total_score = q_sim + a_sim + keyword_boost
            
            if total_score > best_score:
                best_score = total_score
                best_match = faq
        
        return best_match, best_score
    
    def generate_response(self, user_input: str, faqs: List[Dict], 
                         session_id: str = None, threshold: float = 0.35) -> Dict:
        """Generate response with enhanced context awareness"""
        # Add user message to context
        if session_id:
            self.add_to_context(session_id, user_input, 'user')
        
        # Get conversation context for better responses
        conversation_context = self.get_conversation_summary(session_id) if session_id else {}
        
        # Find best match with enhanced context
        best_match, score = self.find_best_match(user_input, faqs, session_id)
        
        if best_match and score >= threshold:
            confidence_level = "high" if score >= 0.7 else "medium" if score >= 0.5 else "low"
            
            # Enhance response with context
            enhanced_reply = self._enhance_response_with_context(
                best_match['answer'], 
                user_input, 
                session_id, 
                conversation_context
            )
            
            response = {
                'reply': enhanced_reply,
                'matched_question': best_match['question'],
                'confidence': score,
                'confidence_level': confidence_level,
                'category': best_match.get('category', 'Umum'),
                'context_aware': True,
                'conversation_summary': conversation_context
            }
            
            # Add response to context
            if session_id:
                self.add_to_context(session_id, enhanced_reply, 'bot')
            
            return response
        else:
            # Generate contextual fallback with conversation awareness
            intent = self.analyze_user_intent(user_input)
            fallback = self.get_contextual_fallback(user_input, intent, faqs, session_id)
            
            # Enhance fallback with conversation context
            enhanced_fallback = self._enhance_fallback_with_context(
                fallback, 
                user_input, 
                session_id, 
                conversation_context
            )
            
            response = {
                'reply': enhanced_fallback,
                'matched_question': None,
                'confidence': score,
                'confidence_level': 'none',
                'category': intent.get('category', 'Unknown'),
                'context_aware': True,
                'conversation_summary': conversation_context
            }
            
            if session_id:
                self.add_to_context(session_id, enhanced_fallback, 'bot')
            
            return response
    
    def _enhance_response_with_context(self, base_response: str, user_input: str, 
                                     session_id: str, context: Dict) -> str:
        """Enhance response with conversation context"""
        if not session_id or not context:
            return base_response
        
        # Check if this is a follow-up question
        is_followup = self.detect_followup_question(user_input, session_id)
        
        if is_followup:
            # Add context-aware introduction
            topics = context.get('topics', [])
            if topics:
                topic_intro = f"Berdasarkan perbincangan tentang {', '.join(topics[-2:])}, "
                return topic_intro + base_response
        
        # Check conversation duration
        duration = context.get('conversation_duration', '')
        if 'minutes' in duration or 'hours' in duration:
            # Add acknowledgment for longer conversations
            return f"Terima kasih kerana terus bertanya. {base_response}"
        
        return base_response
    
    def _enhance_fallback_with_context(self, base_fallback: str, user_input: str, 
                                     session_id: str, context: Dict) -> str:
        """Enhance fallback response with conversation context"""
        if not session_id or not context:
            return base_fallback
        
        # Get conversation topics
        topics = context.get('topics', [])
        if topics:
            # Suggest related topics from conversation
            topic_suggestions = []
            for topic in topics[-2:]:  # Last 2 topics
                if topic == 'zakat':
                    topic_suggestions.append("soalan tentang zakat")
                elif topic == 'nisab':
                    topic_suggestions.append("soalan tentang nisab")
                elif topic == 'pembayaran':
                    topic_suggestions.append("soalan tentang pembayaran")
                elif topic == 'lznk':
                    topic_suggestions.append("soalan tentang LZNK")
            
            if topic_suggestions:
                return f"{base_fallback}\n\nBerdasarkan perbincangan kita, anda juga boleh bertanya tentang {', '.join(topic_suggestions)}."
        
        return base_fallback
    
    def analyze_user_intent(self, user_input: str) -> Dict:
        """Enhanced user intent analysis with better context understanding"""
        text = self.preprocess_text(user_input)
        
        # Enhanced question words and patterns
        question_words = ['apa', 'siapa', 'bagaimana', 'bila', 'mana', 'kenapa', 'berapa',
                         'what', 'who', 'how', 'when', 'where', 'why', 'can', 'could', 'would']
        
        # Enhanced greeting patterns
        greeting_patterns = [
            'assalamualaikum', 'salam', 'hello', 'hi', 'hai', 'good morning', 'good afternoon',
            'good evening', 'selamat', 'apa khabar', 'how are you', 'how do you do'
        ]
        
        # Enhanced thanks patterns
        thanks_patterns = [
            'terima kasih', 'thanks', 'tq', 'thank you', 'thnks', 'thank', 'grateful',
            'appreciate', 'berterima kasih', 'syukur'
        ]
        
        # Enhanced goodbye patterns
        goodbye_patterns = [
            'bye', 'selamat tinggal', 'jumpa lagi', 'goodbye', 'see you', 'farewell',
            'selamat jalan', 'take care', 'bye bye'
        ]
        
        # Detect follow-up questions
        follow_up_indicators = [
            'itu', 'ini', 'tersebut', 'that', 'this', 'it', 'there', 'ada lagi',
            'what about', 'how about', 'boleh tanya lagi', 'one more thing'
        ]
        
        # Detect urgency
        urgency_indicators = [
            'urgent', 'segera', 'cepat', 'now', 'immediately', 'asap', 'terdesak'
        ]
        
        return {
            'is_question': '?' in user_input or any(word in text for word in question_words),
            'is_greeting': any(word in text for word in greeting_patterns),
            'is_thanks': any(word in text for word in thanks_patterns),
            'is_goodbye': any(word in text for word in goodbye_patterns),
            'is_followup': any(word in text for word in follow_up_indicators),
            'is_urgent': any(word in text for word in urgency_indicators),
            'keywords': self.extract_keywords(user_input),
            'category': self.detect_category(text),
            'language': self.detect_language(user_input),
            'sentiment': self.analyze_sentiment(user_input)
        }
    
    def get_contextual_fallback(self, user_input: str, intent: Dict, 
                               faqs: List[Dict], session_id: str = None) -> str:
        """Generate helpful fallback with enhanced context awareness"""
        category = intent.get('category', 'Unknown')
        language = intent.get('language', 'malay')
        sentiment = intent.get('sentiment', 'neutral')
        is_followup = intent.get('is_followup', False)
        is_urgent = intent.get('is_urgent', False)
        
        # Check if this is a follow-up
        is_followup = session_id and self.detect_followup_question(user_input, session_id)
        
        # Generate appropriate response based on language
        if language == 'english':
            return self._generate_english_fallback(category, is_followup, is_urgent, sentiment, faqs, intent['keywords'])
        else:
            return self._generate_malay_fallback(category, is_followup, is_urgent, sentiment, faqs, intent['keywords'])
    
    def _generate_malay_fallback(self, category: str, is_followup: bool, is_urgent: bool, 
                                sentiment: str, faqs: List[Dict], keywords: List[str]) -> str:
        """Generate Malay fallback response"""
        if is_followup:
            return ("Maaf, saya tidak pasti tentang soalan susulan anda. 🤔 "
                   "Boleh cuba tanya dengan lebih spesifik? Contoh: 'Berapa kadar zakat emas?' "
                   "atau 'Bagaimana cara bayar zakat?'")
        
        if is_urgent:
            urgency_prefix = "Saya faham ini penting untuk anda. "
        else:
            urgency_prefix = ""
        
        if sentiment == 'negative':
            empathy = "Saya faham kekeliruan anda. "
        else:
            empathy = ""
        
        fallback_templates = {
            'LZNK': (f"{empathy}{urgency_prefix}Maaf, saya tidak pasti tentang soalan LZNK tersebut. 😔 "
                    "Anda boleh bertanya tentang:\n"
                    "• Perkhidmatan LZNK\n"
                    "• Lokasi pejabat\n"
                    "• Program bantuan\n"
                    "• Cara menghubungi LZNK"),
            'Pembayaran': (f"{empathy}{urgency_prefix}Maaf, saya tidak dapat membantu dengan soalan pembayaran tersebut. 💳 "
                         "Anda boleh bertanya:\n"
                         "• Cara membayar zakat\n"
                         "• Kaedah pembayaran\n"
                         "• Waktu pembayaran"),
            'Nisab': (f"{empathy}{urgency_prefix}Maaf, saya tidak pasti tentang soalan nisab tersebut. 📊 "
                     "Anda boleh bertanya:\n"
                     "• Nisab emas\n"
                     "• Nisab wang simpanan\n"
                     "• Kadar zakat"),
            'Asnaf': (f"{empathy}{urgency_prefix}Maaf, saya tidak pasti tentang soalan asnaf tersebut. 👥 "
                     "Anda boleh bertanya:\n"
                     "• Siapa yang layak menerima zakat\n"
                     "• Golongan asnaf\n"
                     "• Syarat penerima zakat"),
            'Bantuan': (f"{empathy}{urgency_prefix}Maaf, saya tidak pasti tentang soalan bantuan tersebut. 🤝 "
                       "Anda boleh bertanya:\n"
                       "• Cara memohon bantuan\n"
                       "• Jenis bantuan yang tersedia\n"
                       "• Syarat kelayakan bantuan")
        }
        
        if category in fallback_templates:
            return fallback_templates[category]
        
        # Get suggested questions
        suggestions = self.get_suggested_questions(faqs, keywords)
        if suggestions:
            return (f"{empathy}{urgency_prefix}Maaf, saya tidak pasti tentang soalan tersebut. 🤔 "
                   f"Mungkin anda ingin tahu tentang:\n• {suggestions[0]}")
        
        return (f"{empathy}{urgency_prefix}Maaf, saya tidak dapat memahami soalan anda. 😔 "
               "Bolehkah anda cuba soalan lain tentang zakat atau LZNK? "
               "Contoh: 'Apa itu zakat?' atau 'Bagaimana cara bayar zakat?'")
    
    def _generate_english_fallback(self, category: str, is_followup: bool, is_urgent: bool, 
                                  sentiment: str, faqs: List[Dict], keywords: List[str]) -> str:
        """Generate English fallback response"""
        if is_followup:
            return ("I'm not sure about your follow-up question. 🤔 "
                   "Could you try asking more specifically? For example: 'What is the zakat rate for gold?' "
                   "or 'How do I pay zakat?'")
        
        if is_urgent:
            urgency_prefix = "I understand this is important to you. "
        else:
            urgency_prefix = ""
        
        if sentiment == 'negative':
            empathy = "I understand your confusion. "
        else:
            empathy = ""
        
        fallback_templates = {
            'LZNK': (f"{empathy}{urgency_prefix}I'm not sure about that LZNK question. 😔 "
                    "You can ask about:\n"
                    "• LZNK services\n"
                    "• Office locations\n"
                    "• Assistance programs\n"
                    "• How to contact LZNK"),
            'Pembayaran': (f"{empathy}{urgency_prefix}I can't help with that payment question. 💳 "
                         "You can ask about:\n"
                         "• How to pay zakat\n"
                         "• Payment methods\n"
                         "• Payment timing"),
            'Nisab': (f"{empathy}{urgency_prefix}I'm not sure about that nisab question. 📊 "
                     "You can ask about:\n"
                     "• Gold nisab\n"
                     "• Savings nisab\n"
                     "• Zakat rates"),
            'Asnaf': (f"{empathy}{urgency_prefix}I'm not sure about that asnaf question. 👥 "
                     "You can ask about:\n"
                     "• Who is eligible to receive zakat\n"
                     "• Asnaf categories\n"
                     "• Recipient requirements"),
            'Bantuan': (f"{empathy}{urgency_prefix}I'm not sure about that assistance question. 🤝 "
                       "You can ask about:\n"
                       "• How to apply for assistance\n"
                       "• Available assistance types\n"
                       "• Eligibility requirements")
        }
        
        if category in fallback_templates:
            return fallback_templates[category]
        
        # Get suggested questions
        suggestions = self.get_suggested_questions(faqs, keywords)
        if suggestions:
            return (f"{empathy}{urgency_prefix}I'm not sure about that question. 🤔 "
                   f"Maybe you'd like to know about:\n• {suggestions[0]}")
        
        return (f"{empathy}{urgency_prefix}I can't understand your question. 😔 "
               "Could you try asking something else about zakat or LZNK? "
               "For example: 'What is zakat?' or 'How do I pay zakat?'")
    
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
    
    def detect_language(self, text: str) -> str:
        """Detect the primary language of the input"""
        malay_indicators = [
            'apa', 'siapa', 'bagaimana', 'bila', 'mana', 'kenapa', 'berapa',
            'zakat', 'nisab', 'haul', 'bayar', 'pembayaran', 'lembaga',
            'assalamualaikum', 'terima kasih', 'selamat', 'jumpa'
        ]
        
        english_indicators = [
            'what', 'who', 'how', 'when', 'where', 'why', 'can', 'could',
            'zakat', 'nisab', 'haul', 'pay', 'payment', 'office', 'location',
            'hello', 'hi', 'thanks', 'goodbye', 'see you'
        ]
        
        text_lower = text.lower()
        malay_count = sum(1 for word in malay_indicators if word in text_lower)
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        if malay_count > english_count:
            return 'malay'
        elif english_count > malay_count:
            return 'english'
        else:
            return 'mixed'
    
    def analyze_sentiment(self, text: str) -> str:
        """Analyze the sentiment of the user input"""
        positive_words = [
            'terima kasih', 'thanks', 'good', 'bagus', 'excellent', 'wonderful',
            'helpful', 'useful', 'great', 'amazing', 'fantastic'
        ]
        
        negative_words = [
            'problem', 'issue', 'error', 'wrong', 'bad', 'teruk', 'buruk',
            'difficult', 'susah', 'confused', 'confusing', 'frustrated'
        ]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def detect_category(self, text: str) -> str:
        """Enhanced category detection with more specific categories"""
        category_keywords = {
            'LZNK': ['lznk', 'lembaga', 'kedah', 'pejabat', 'lokasi', 'office', 'location', 'cawangan', 'branch'],
            'Pembayaran': ['bayar', 'pembayaran', 'cara', 'kaedah', 'pay', 'payment', 'method', 'portal', 'online'],
            'Nisab': ['nisab', 'nilai', 'kadar', 'jumlah', 'threshold', 'rate', 'minimum', 'minimum amount'],
            'Perniagaan': ['perniagaan', 'niaga', 'bisnes', 'business', 'company', 'syarikat', 'enterprise'],
            'Haul': ['haul', 'tahun', 'tempoh', 'year', 'period', 'duration', 'masa'],
            'Asnaf': ['asnaf', 'penerima', 'recipient', 'beneficiary', 'layak', 'eligible'],
            'Bantuan': ['bantuan', 'help', 'assistance', 'aid', 'support', 'tolong', 'mohon', 'apply'],
            'Emas': ['emas', 'gold', 'jewelry', 'perhiasan', 'barang kemas'],
            'Wang': ['wang', 'duit', 'money', 'cash', 'simpanan', 'savings', 'deposit']
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in text for kw in keywords):
                return category
        
        return 'Umum'
    
    def clear_session_context(self, session_id: str):
        """Clear conversation context for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
        if session_id in self.context_keywords:
            del self.context_keywords[session_id]
        if session_id in self.conversation_topics:
            del self.conversation_topics[session_id]
        if session_id in self.user_preferences:
            del self.user_preferences[session_id]
        if session_id in self.conversation_entities:
            del self.conversation_entities[session_id]
    
    def get_conversation_insights(self, session_id: str) -> Dict:
        """Get insights about the conversation"""
        context = self.get_conversation_summary(session_id)
        if not context:
            return {}
        
        insights = {
            'conversation_length': context.get('message_count', 0),
            'topics_discussed': context.get('topics', []),
            'duration': context.get('conversation_duration', ''),
            'user_engagement': self._calculate_engagement_score(session_id),
            'conversation_flow': self._analyze_conversation_flow(session_id),
            'key_entities': list(self.conversation_entities[session_id]) if session_id in self.conversation_entities else []
        }
        
        return insights
    
    def _calculate_engagement_score(self, session_id: str) -> str:
        """Calculate user engagement score"""
        history = self.get_conversation_history(session_id)
        if not history:
            return "low"
        
        user_messages = [msg for msg in history if msg['role'] == 'user']
        if len(user_messages) < 3:
            return "low"
        elif len(user_messages) < 7:
            return "medium"
        else:
            return "high"
    
    def _analyze_conversation_flow(self, session_id: str) -> str:
        """Analyze the flow of the conversation"""
        history = self.get_conversation_history(session_id)
        if len(history) < 3:
            return "starting"
        
        # Check for question patterns
        recent_messages = history[-3:]
        question_count = sum(1 for msg in recent_messages if msg['role'] == 'user' and '?' in msg['message'])
        
        if question_count >= 2:
            return "questioning"
        elif any('terima kasih' in msg['message'].lower() for msg in recent_messages if msg['role'] == 'user'):
            return "grateful"
        else:
            return "discussing"
    
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