// ============================================
// ZAKIA CHATBOT - SMART ESCALATION VERSION
// ============================================

if (!window.ZakiaChatbot) {
    class ZakiaChatbot {
        constructor() {
            this.messagesEl = document.getElementById("messages");
            this.inputEl = document.getElementById("userInput");
            this.typingEl = document.getElementById("typing");
            this.sendBtn = document.getElementById("sendBtn");
            this.endBtn = document.getElementById("endChat");
            this.quickRepliesEl = document.getElementById("quickReplies");
            this.minimizeBtn = document.querySelector('.minimize-btn');
            this.chatbox = document.querySelector('.chatbox');

            this.sessionId = null;
            this.hasUserSentMessage = false;
            this.apiBaseUrl = window.CONFIG.API_BASE_URL;
            this.isMinimized = false;

            // Smart escalation properties
            this.conversationHistory = [];
            this.escalationOffered = false;
            this.lastTriggerType = null;
            this.confusionSignalCount = 0;
            this.repetitionCount = 0;
            this.lastUserMessage = '';

            // Initialize voice handler AFTER DOM is ready
            this.voiceHandler = null;

            // Initialize zakat handler
            this.zakatHandler = null;

            this.init();
        }

        init() {
            console.log('🚀 Initializing ZAKIA Chatbot...');
            
            this.setupEventListeners();
            this.loadFAQs();

            // Initialize feature handlers
            this.initializeHandlers();
            
            console.log('✅ ZAKIA Chatbot initialized successfully');
        }

        /**
         * Initialize all feature handlers
         */
        initializeHandlers() {
            setTimeout(() => {
                // Initialize Voice Handler
                if (window.VoiceHandler) {
                    console.log('🎤 Initializing Voice Handler...');
                    this.voiceHandler = new VoiceHandler(this);
                    console.log('✅ Voice Handler initialized');
                } else {
                    console.warn('⚠️ VoiceHandler not found. Voice features disabled.');
                }
                
                // Initialize Zakat Handler
                if (window.ZakatHandler) {
                    console.log('🧮 Initializing Zakat Handler...');
                    this.zakatHandler = new window.ZakatHandler(this);
                    window.zakatHandler = this.zakatHandler;
                    console.log('✅ Zakat Handler initialized');
                } else {
                    console.warn('⚠️ ZakatHandler not found.');
                }
                
                // Initialize FAQ Browser
                if (window.FAQBrowser) {
                    console.log('📚 FAQ Browser available');
                }
            }, 100);
        }

        setupEventListeners() {
            this.sendBtn.addEventListener('click', () => this.sendMessage());
            this.inputEl.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            this.quickRepliesEl.addEventListener('click', (e) => {
                const target = e.target;
                if (target.classList.contains('quick-reply')) {
                    this.handleQuickReplyClick(target);
                }
            });

            this.endBtn.addEventListener('click', () => this.endChat());
            this.minimizeBtn.addEventListener('click', () => this.toggleMinimize());
        }

        toggleMinimize() {
            this.isMinimized = !this.isMinimized;

            if (this.isMinimized) {
                this.chatbox.style.display = 'none';
                if (!document.getElementById('chatWidget')) {
                    this.createMinimizedWidget();
                }
            } else {
                this.chatbox.style.display = 'flex';
                const widget = document.getElementById('chatWidget');
                if (widget) {
                    widget.remove();
                }
            }
        }

        createMinimizedWidget() {
            const widget = document.createElement('div');
            widget.id = 'chatWidget';
            widget.innerHTML = `
                <img src="images/zakia-avatar.png" alt="ZAKIA" class="widget-avatar">
                <div class="widget-content">
                    <div class="widget-title">Hi, saya ZAKIA</div>
                    <div class="widget-subtitle">Nak tanya soalan tentang zakat?</div>
                </div>
            `;

            const self = this;
            widget.addEventListener('click', function () {
                self.isMinimized = false;
                self.chatbox.style.display = 'flex';
                widget.remove();
            });

            document.body.appendChild(widget);
        }

        appendMessage(text, sender, isHTML = false, options = {}) {
            const msg = document.createElement('div');
            msg.className = `msg ${sender}`;

            if (options.messageId) {
                msg.dataset.messageId = options.messageId;
            }

            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            });

            const content = isHTML ? text : this.processLinks(text);

            if (sender === 'bot') {
                msg.innerHTML = `
                    <img src="images/zakia-avatar.png" class="msg-avatar" alt="ZAKIA">
                    <div class="bubble-container">
                        <div class="bubble bot-bubble">${content}</div>
                        <div class="msg-time">${timeString}</div>
                    </div>
                `;
                
                // Trigger TTS for bot messages (if voice handler is available and not skipped)
                if (this.voiceHandler && !options.skipTTS) {
                    const plainText = this.getPlainTextFromHTML(content);
                    this.voiceHandler.handleBotMessage(plainText);
                }
                
                // Track message for history
                this.conversationHistory.push({
                    role: 'bot',
                    content: this.getPlainTextFromHTML(content),
                    timestamp: now
                });
            } else {
                msg.innerHTML = `
                    <div class="bubble-container">
                        <div class="bubble user-bubble">${content}</div>
                        <div class="msg-time">${timeString}</div>
                    </div>
                `;
                
                // Track user message
                this.conversationHistory.push({
                    role: 'user',
                    content: text,
                    timestamp: now
                });
            }

            this.messagesEl.appendChild(msg);
            this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
            // tell voice handler about new bot message element so indicator attaches correctly
            if (sender === 'bot' && this.voiceHandler && !options.skipTTS) {
                const plainText = this.getPlainTextFromHTML(content);
                this.voiceHandler.handleBotMessage(plainText, msg);
            }
            return msg;
        }

        /**
         * Extract plain text from HTML for TTS
         */
        getPlainTextFromHTML(html) {
            const temp = document.createElement('div');
            temp.innerHTML = html;
            return temp.textContent || temp.innerText || '';
        }

        // ========================================
        // SMART ESCALATION TRIGGERS
        // ========================================
        
        checkEscalationTriggers(userMessage, botResponse) {
            const triggers = [];
            
            // 1. EXPLICIT REQUEST
            if (this.detectExplicitRequest(userMessage)) {
                triggers.push('explicit_request');
            }
            
            // 2. CONFUSION SIGNALS
            if (this.detectConfusion(userMessage)) {
                this.confusionSignalCount++;
                if (this.confusionSignalCount >= 2) {
                    triggers.push('confusion');
                }
            } else {
                this.confusionSignalCount = 0;
            }
            
            // 3. REPETITIVE QUERIES
            if (this.detectRepetition()) {
                triggers.push('repetition');
            }
            
            // 4. COMPLEX QUERIES
            if (this.detectComplexity(userMessage)) {
                triggers.push('complexity');
            }
            
            // Offer escalation if ANY trigger fires and not already offered recently
            if (triggers.length > 0 && !this.escalationOffered) {
                console.log('🎯 Escalation triggers fired:', triggers);
                this.lastTriggerType = triggers[0];
                this.offerEscalation(triggers[0]);
                this.escalationOffered = true;
                
                // Reset flag after 2 minutes
                setTimeout(() => {
                    this.escalationOffered = false;
                }, 120000);
            }
        }
        
        detectExplicitRequest(message) {
            const humanKeywords = [
                'bercakap dengan manusia', 'cakap dengan pegawai', 
                'call saya', 'hubungi saya', 'jumpa staff',
                'nak bercakap dengan orang', 'contact admin',
                'speak to human', 'talk to person', 'jumpa staf'
            ];
            const lower = message.toLowerCase();
            return humanKeywords.some(kw => lower.includes(kw));
        }
        
        detectConfusion(message) {
            const confusionSignals = [
                'tak faham', 'tak jelas', 'huh', 'blur',
                'confuse', 'complicated', 'susah faham', 'what do you mean',
                'tidak faham', 'kurang jelas',
            ];
            const lower = message.toLowerCase();
            return confusionSignals.some(s => lower.includes(s));
        }
        
        detectRepetition() {
            const recentUserMessages = this.conversationHistory
                .filter(m => m.role === 'user')
                .slice(-3);
            
            if (recentUserMessages.length < 3) return false;
            
            const keywords1 = this.extractKeywords(recentUserMessages[0].content);
            const keywords2 = this.extractKeywords(recentUserMessages[1].content);
            const keywords3 = this.extractKeywords(recentUserMessages[2].content);
            
            const overlap12 = this.calculateOverlap(keywords1, keywords2);
            const overlap23 = this.calculateOverlap(keywords2, keywords3);
            const overlap13 = this.calculateOverlap(keywords1, keywords3);
            
        
            return overlap12 > 0.5 && overlap23 > 0.5 && overlap13 > 0.5;
        }
        
        detectComplexity(message) {
            const complexIndicators = [
                'kes khas', 'situasi saya', 'macam mana kalau',
                'boleh ke kalau', 'specific case', 'in my case',
                'special situation', 'my circumstances',
                'bagaimana jika', 'adakah boleh', 'case saya'
            ];
            const lower = message.toLowerCase();
            return complexIndicators.some(ind => lower.includes(ind));
        }
        
        extractKeywords(text) {
            const stopwords = ['saya', 'nak', 'apa', 'bila', 'ke', 'dan', 'atau', 'the', 'is', 'a', 'to', 'yang'];
            return text.toLowerCase()
                .split(/\s+/)
                .filter(word => word.length > 3 && !stopwords.includes(word));
        }
        
        calculateOverlap(arr1, arr2) {
            const set1 = new Set(arr1);
            const set2 = new Set(arr2);
            const intersection = [...set1].filter(x => set2.has(x));
            return intersection.length / Math.max(arr1.length, arr2.length, 1);
        }
        
        offerEscalation(triggerType) {
            const messages = {
                explicit_request: `Baik, saya faham anda ingin bercakap dengan pegawai kami. Sila isi borang ringkas dan kami akan hubungi anda. 🤝`,
                confusion: `Saya nampak anda mungkin perlukan penjelasan yang lebih terperinci. Pegawai kami boleh membantu dengan lebih mendalam. 📞`,
                repetition: `Saya perasan anda ada soalan berulang tentang topik ini. Mungkin lebih baik jika pegawai kami terangkan secara langsung? 💬`,
                complexity: `Kes anda nampaknya memerlukan penelitian khusus. Pegawai LZNK boleh semak dan beri jawapan yang tepat untuk situasi anda. ✅`,
                low_confidence: `Untuk memastikan anda dapat maklumat yang paling tepat, saya cadangkan bercakap dengan pegawai kami. 👨‍💼`
            };
            
            const message = messages[triggerType] || messages.explicit_request;
            
            this.appendMessage(message, 'bot', false, { skipFeedback: true, skipTTS: false });
            
            setTimeout(() => {
                this.showEscalationButtons();
            }, 500);
        }
        
        showEscalationButtons() {
            const buttonsHtml = `
                <div class="escalation-options">
                    <button class="escalation-btn yes-btn" onclick="window.zakiaInstance.openContactForm()">Hubungi Pegawai LZNK</button>
                    <button class="escalation-btn no-btn" onclick="window.zakiaInstance.dismissEscalation()">Tidak, saya faham sekarang</button>
                </div>
            `;
            
            this.appendMessage(buttonsHtml, 'bot', true, { skipFeedback: true, skipTTS: true });
        }

        dismissEscalation() {
            this.appendMessage("Baik! Jika ada soalan lain, saya sedia membantu. 😊", 'bot', false, { skipFeedback: true });
            this.escalationOffered = false;
        }

        // ========================================
        // CONTACT FORM MODAL
        // ========================================
        
        openContactForm() {
            let modal = document.getElementById('contactFormModal');
            
            if (!modal) {
                modal = this.createContactFormModal();
                document.body.appendChild(modal);
            }
            
            modal.style.display = 'flex';
            
            setTimeout(() => {
                const nameInput = modal.querySelector('#contactName');
                if (nameInput) nameInput.focus();
            }, 100);
        }
        
        createContactFormModal() {
            const modal = document.createElement('div');
            modal.id = 'contactFormModal';
            modal.className = 'contact-form-modal';
            
            modal.innerHTML = `
                <div class="modal-overlay" onclick="window.zakiaInstance.closeContactForm()"></div>
                <div class="modal-content-contact">
                    <div class="modal-header-contact">
                        <h2>📋 Hubungi Pegawai LZNK</h2>
                        <button class="modal-close-contact" onclick="window.zakiaInstance.closeContactForm()">×</button>
                    </div>
                    
                    <form id="contactRequestForm" class="contact-form">
                        <div class="form-group">
                            <label for="contactName">Nama <span class="required">*</span></label>
                            <input type="text" id="contactName" name="name" required placeholder="Nama penuh anda">
                        </div>
                        
                        <div class="form-group">
                            <label for="contactPhone">No. Telefon <span class="required">*</span></label>
                            <input type="tel" id="contactPhone" name="phone" required placeholder="+60123456789" pattern="[+]?[0-9]{10,15}">
                            <small class="form-help">Contoh: +60123456789 atau 0123456789</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="contactEmail">Email</label>
                            <input type="email" id="contactEmail" name="email" placeholder="email@example.com">
                        </div>
                        
                        <div class="form-group">
                            <label for="contactQuestion">Soalan/Masalah Anda <span class="required">*</span></label>
                            <textarea id="contactQuestion" name="question" rows="5" required placeholder="Terangkan soalan atau masalah anda dengan lebih terperinci..."></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label>Cara Dihubungi </label>
                            <div class="radio-group">
                                <label>
                                    <input type="radio" name="preferred_method" value="whatsapp" checked>
                                    <span>💬 WhatsApp</span>
                                </label>
                                <label>
                                    <input type="radio" name="preferred_method" value="phone">
                                    <span>📞 Telefon</span>
                                </label>
                                <label>
                                    <input type="radio" name="preferred_method" value="email">
                                    <span>📧 Email</span>
                                </label>
                            </div>
                        </div>
                        
                        <div class="office-hours-info">
                            <strong>⏰ Waktu Operasi:</strong>
                            <br>Ahad - Rabu: 9:00 pagi - 5:00 petang
                            <br>Khamis: 9:00 pagi - 3:30 petang
                            <br>Jumaat & Sabtu: Cuti
                        </div>
                        
                        <div class="form-actions">
                            <button type="submit" class="btn-submit-contact">📤 Hantar Permintaan</button>
                        </div>
                    </form>
                    
                    <div id="contactFormSuccess" class="contact-success" style="display: none;">
                        <div class="success-icon">✅</div>
                        <h3>Permintaan Dihantar!</h3>
                        <p id="successMessage"></p>
                        <p class="reference-number">Nombor Rujukan: <strong id="referenceNumber"></strong></p>
                        <button onclick="window.zakiaInstance.closeContactForm()" class="btn-close-success">Tutup</button>
                    </div>
                </div>
            `;
            
            setTimeout(() => {
                const form = modal.querySelector('#contactRequestForm');
                const emailInput = modal.querySelector('#contactEmail');
                if (form) {
                    const radios = form.querySelectorAll('input[name="preferred_method"]');
                    radios.forEach(r => {
                        r.addEventListener('change', () => {
                            if (emailInput) {
                                emailInput.required = (r.value === 'email');
                            }
                        });
                    });

                    form.addEventListener('submit', (e) => {
                        e.preventDefault();
                        this.submitContactRequest(form);
                    });
                }
            }, 0);
            
            return modal;
        }
        
        async submitContactRequest(form) {
            const formData = new FormData(form);
            const preferred = formData.get('preferred_method');
            const emailVal = formData.get('email') || '';

            // quick client-side validation for mandatory email when email contact selected
            if (preferred === 'email' && emailVal.trim() === '') {
                alert('Sila isi alamat email jika memilih cara dihubungi melalui email.');
                return;
            }

            const data = {
                session_id: this.sessionId,
                name: formData.get('name'),
                phone: formData.get('phone'),
                email: emailVal || null,
                question: formData.get('question'),
                preferred_method: preferred,
                conversation_history: this.conversationHistory.slice(-5),
                trigger_type: this.lastTriggerType
            };
            
            const submitBtn = form.querySelector('.btn-submit-contact');
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Menghantar...';
            
            try {
                const response = await fetch(`${this.apiBaseUrl}${window.CONFIG.ENDPOINTS.CONTACT_REQUEST}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    form.style.display = 'none';
                    
                    const successDiv = document.getElementById('contactFormSuccess');
                    const successMsg = document.getElementById('successMessage');
                    const refNum = document.getElementById('referenceNumber');
                    
                    successMsg.textContent = result.message;
                    refNum.textContent = `#${result.request_id}`;
                    
                    successDiv.style.display = 'block';
                    
                    this.appendMessage(
                        result.is_office_hours 
                            ? `✅ Terima kasih! Pegawai kami akan hubungi anda dalam masa 2-4 jam bekerja. Nombor rujukan: #${result.request_id}`
                            : `🌙 Terima kasih! Permintaan anda telah diterima. Pegawai kami akan hubungi anda pada hari bekerja berikutnya. Nombor rujukan: #${result.request_id}`,
                        'bot',
                        false,
                        { skipFeedback: true }
                    );
                } else {
                    throw new Error(result.error || 'Failed to submit request');
                }
            } catch (error) {
                console.error('❌ Contact request error:', error);
                alert('Maaf, gagal menghantar permintaan. Sila cuba lagi.');
                submitBtn.disabled = false;
                submitBtn.textContent = '📤 Hantar Permintaan';
            }
        }
        
        closeContactForm() {
            const modal = document.getElementById('contactFormModal');
            if (modal) {
                modal.style.display = 'none';
                
                const form = modal.querySelector('#contactRequestForm');
                const successDiv = modal.querySelector('#contactFormSuccess');
                
                if (form) {
                    form.reset();
                    form.style.display = 'block';
                }
                
                if (successDiv) {
                    successDiv.style.display = 'none';
                }
                
                const submitBtn = modal.querySelector('.btn-submit-contact');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '📤 Hantar Permintaan';
                }
            }
        }

        processLinks(text) {
            let processed = this.escapeHtml(text);

            const htmlLinkPattern = /&lt;a\s+href=&quot;([^&]+)&quot;[^&]*&gt;([^&]+)&lt;\/a&gt;/gi;
            processed = processed.replace(htmlLinkPattern, (match, url, label) => {
                const cleanUrl = url.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"');
                const cleanLabel = label.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
                return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="chat-link">${cleanLabel}</a>`;
            });

            const urlPattern = /(https?:\/\/[^\s<>"]+[^\s<>".,;:!?)])/gi;
            processed = processed.replace(urlPattern, (url) => {
                const displayUrl = url.length > 50 ? url.substring(0, 47) + '...' : url;
                return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="chat-link">${displayUrl}</a>`;
            });

            const phonePattern = /(\+?[\d\s\-()]{10,})/g;
            processed = processed.replace(phonePattern, (phone) => {
                const cleanPhone = phone.replace(/[\s\-()]/g, '');
                if (cleanPhone.length >= 10) {
                    return `<a href="tel:${cleanPhone}" class="chat-link">${phone}</a>`;
                }
                return phone;
            });

            const emailPattern = /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g;
            processed = processed.replace(emailPattern, (email) => {
                return `<a href="mailto:${email}" class="chat-link">${email}</a>`;
            });

            return processed;
        }

        setTyping(isTyping) {
            this.typingEl.classList.toggle('hidden', !isTyping);
        }

        escapeHtml(str) {
            return str
                .replaceAll('&', '&amp;')
                .replaceAll('<', '&lt;')
                .replaceAll('>', '&gt;');
        }

        hideQuickReplies() {
            this.quickRepliesEl.style.display = 'none';
        }

        showQuickReplies() {
            this.quickRepliesEl.style.display = 'flex';
        }

        async sendMessage(messageOverride) {
            const text = (messageOverride ?? this.inputEl.value).trim();
            if (!text) return;

            this.appendMessage(text, 'user');
            this.inputEl.value = '';
            this.sendBtn.disabled = true;
            this.hideQuickReplies();

            this.hasUserSentMessage = true;
            this.lastUserMessage = text;

            // Priority 1: Check if reminder handler is active
            if (this.zakatHandler && this.zakatHandler.reminderHandler &&
                this.zakatHandler.reminderHandler.isActive()) {
                const handled = await this.zakatHandler.reminderHandler.processInput(text);
                if (handled) {
                    this.sendBtn.disabled = false;
                    return;
                }
            }

            // Priority 2: Check if zakat handler is active
            if (this.zakatHandler && this.zakatHandler.state.active) {
                if (text.toLowerCase().includes('batal') || text.toLowerCase().includes('cancel')) {
                    this.zakatHandler.cancel();
                    this.sendBtn.disabled = false;
                    return;
                }

                const handled = this.zakatHandler.processInput(text);
                if (handled) {
                    this.sendBtn.disabled = false;
                    return;
                }
            }

            // Priority 3: Check for new zakat intent
            if (this.zakatHandler) {
                const zakatIntent = this.zakatHandler.detectZakatIntent(text);
                if (zakatIntent) {
                    if (zakatIntent === 'menu') {
                        setTimeout(() => {
                            this.zakatHandler.showZakatMenu();
                        }, 500);
                        this.sendBtn.disabled = false;
                        return;
                    } else if (zakatIntent === 'nisab') {
                        this.zakatHandler.fetchNisabInfo();
                        this.sendBtn.disabled = false;
                        return;
                    } else {
                        setTimeout(() => {
                            this.zakatHandler.startZakatCalculation(zakatIntent);
                        }, 500);
                        this.sendBtn.disabled = false;
                        return;
                    }
                }
            }

            // Priority 4: Regular chat processing
            this.setTyping(true);

            try {
                const requestBody = { message: text };
                if (this.sessionId) {
                    requestBody.session_id = this.sessionId;
                }

                const res = await fetch(`${this.apiBaseUrl}${window.CONFIG.ENDPOINTS.CHAT}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(requestBody)
                });

                const data = await res.json();

                if (data.session_id) {
                    this.sessionId = data.session_id;
                }

                const botResponse = data.reply || window.CONFIG.MESSAGES.SERVER_ERROR;
                this.appendMessage(botResponse, 'bot');

                // CHECK ESCALATION TRIGGERS AFTER BOT RESPONSE
                this.checkEscalationTriggers(text, {
                    content: botResponse,
                    confidence: data.confidence
                });

                if (!this.hasUserSentMessage) {
                    setTimeout(() => this.showQuickReplies(), window.CONFIG.UI.TYPING_DELAY);
                }

            } catch (e) {
                console.error('❌ Error sending message:', e);
                this.appendMessage(window.CONFIG.MESSAGES.CONNECTION_ERROR, 'bot');
                if (!this.hasUserSentMessage) {
                    this.showQuickReplies();
                }
            } finally {
                this.setTyping(false);
                this.sendBtn.disabled = false;
                this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
            }
        }

        handleQuickReplyClick(target) {
            document.querySelectorAll('.quick-reply').forEach(btn => {
                btn.classList.remove('selected');
            });

            target.classList.add('selected');

            setTimeout(() => {
                target.classList.remove('selected');
            }, window.CONFIG.UI.QUICK_REPLY_SELECTION_DURATION);

            this.sendMessage(target.getAttribute('data-text'));
        }

        endChat() {
            // Stop any ongoing TTS
            if (this.voiceHandler) {
                this.voiceHandler.stopSpeaking();
            }
            
            this.messagesEl.innerHTML = '';
            this.sessionId = null;
            this.hasUserSentMessage = false;
            
            // Reset escalation state
            this.conversationHistory = [];
            this.escalationOffered = false;
            this.confusionSignalCount = 0;
            this.repetitionCount = 0;

            // Reset zakat handler
            if (this.zakatHandler) {
                this.zakatHandler.resetState();
            }

            this.appendMessage(window.CONFIG.MESSAGES.SESSION_ENDED, 'bot', false, { skipFeedback: true, skipTTS: true });
            this.hideQuickReplies();
        }

        async loadFAQs() {
            try {
                const res = await fetch(`${this.apiBaseUrl}${window.CONFIG.ENDPOINTS.FAQS}`);
                const data = await res.json();

                if (data.faqs && data.faqs.length > 0) {
                    console.log(`✅ Loaded ${data.faqs.length} FAQs`);
                }
            } catch (e) {
                console.log('Could not load FAQs:', e);
            }
        }
    }

    window.ZakiaChatbot = ZakiaChatbot;
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 DOM loaded - Creating ZAKIA chatbot instance...');
    window.zakiaInstance = new ZakiaChatbot();
    window.chatbotInstance = window.zakiaInstance;
    
    console.log('✅ ZAKIA Chatbot instance created and exposed globally');
});