// Prevent redeclaration when script loaded multiple times
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

            // Initialize voice handler AFTER DOM is ready
            this.voiceHandler = null;

            // Live chat state
            this.waitingForAdmin = false;
            this.pollInterval = null;
            this.adminWaitingMessageId = null;

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
            // Wait a bit to ensure all scripts are loaded
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

            // Store message ID for later reference
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
                
                // Only add feedback controls if NOT an admin response and NOT waiting for admin
                if (!options.isAdminResponse && !options.skipFeedback) {
                    this.addFeedbackControls(msg, content);
                }
                
                // Trigger TTS for bot messages (if voice handler is available and not skipped)
                if (this.voiceHandler && !options.skipTTS) {
                    // Get plain text without HTML for TTS
                    const plainText = this.getPlainTextFromHTML(content);
                    this.voiceHandler.handleBotMessage(plainText);
                }
            } else {
                msg.innerHTML = `
                    <div class="bubble-container">
                        <div class="bubble user-bubble">${content}</div>
                        <div class="msg-time">${timeString}</div>
                    </div>
                `;
            }

            this.messagesEl.appendChild(msg);
            this.messagesEl.scrollTop = this.messagesEl.scrollHeight;

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

        addFeedbackControls(msgEl, botText) {
            // Avoid duplicate controls
            if (msgEl.querySelector('.feedback-row')) return;

            const feedbackRow = document.createElement('div');
            feedbackRow.className = 'feedback-row';
            feedbackRow.innerHTML = `
                <span class="feedback-label">Jawapan ini membantu?</span>
                <button class="feedback-btn yes">👍 Ya</button>
                <button class="feedback-btn no">❌ Tidak</button>
            `;

            const bubbleContainer = msgEl.querySelector('.bubble-container');
            if (bubbleContainer) {
                bubbleContainer.appendChild(feedbackRow);
            } else {
                msgEl.appendChild(feedbackRow);
            }

            const yesBtn = feedbackRow.querySelector('.yes');
            const noBtn = feedbackRow.querySelector('.no');

            const disableButtons = () => {
                yesBtn.disabled = true;
                noBtn.disabled = true;
                yesBtn.classList.add('disabled');
                noBtn.classList.add('disabled');
            };

            yesBtn.addEventListener('click', () => {
                this.appendMessage("Terima kasih atas maklum balas! 😊", 'bot', false, { skipFeedback: true });
                disableButtons();
            });

            noBtn.addEventListener('click', async () => {
                disableButtons();
                await this.escalateToLiveChat(botText);
            });
        }

        showAdminWaitingIndicator() {
            const messageId = 'admin-waiting-' + Date.now();
            
            const waitingMsg = this.appendMessage(
                `<div class="admin-waiting-indicator">
                    <div class="waiting-spinner"></div>
                    <p>Menunggu jawapan dari admin...</p>
                    <small>Ini mungkin mengambil masa beberapa minit</small>
                </div>`,
                'bot',
                true,
                { messageId, skipFeedback: true, skipTTS: true }
            );

            this.adminWaitingMessageId = messageId;
            return waitingMsg;
        }

        removeAdminWaitingIndicator() {
            if (this.adminWaitingMessageId) {
                const waitingMsg = this.messagesEl.querySelector(`[data-message-id="${this.adminWaitingMessageId}"]`);
                if (waitingMsg) {
                    waitingMsg.remove();
                }
                this.adminWaitingMessageId = null;
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
                // Check for cancel command
                if (text.toLowerCase().includes('batal') || text.toLowerCase().includes('cancel')) {
                    this.zakatHandler.cancel();
                    this.sendBtn.disabled = false;
                    return;
                }

                // Process zakat input
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

        async escalateToLiveChat(botReplyText) {
            try {
                console.log('\n📤 ESCALATING TO LIVE CHAT');
                console.log('   Session ID:', this.sessionId);
                console.log('   User Message:', this.lastUserMessage);

                const payload = {
                    session_id: this.sessionId,
                    user_message: this.lastUserMessage || '',
                    bot_response: botReplyText || ''
                };

                const res = await fetch(`${this.apiBaseUrl}${window.CONFIG.ENDPOINTS.LIVE_CHAT_REQUEST}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                console.log('📨 Escalation response:', data);

                if (data.success) {
                    console.log('✅ Escalation successful, request ID:', data.id);
                    
                    // Show waiting indicator
                    this.showAdminWaitingIndicator();
                    
                    // Start polling for admin response
                    this.waitingForAdmin = true;
                    this.startAdminResponsePolling();
                } else {
                    console.error('❌ Escalation failed:', data.error);
                    this.appendMessage("Maaf, tidak dapat hantar permintaan live chat. Sila cuba lagi.", 'bot', false, { skipFeedback: true });
                }
            } catch (error) {
                console.error('❌ Live chat request error:', error);
                this.appendMessage("Ralat menghantar permintaan live chat. Sila cuba lagi.", 'bot', false, { skipFeedback: true });
            }
        }

        startAdminResponsePolling() {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
            }
            
            console.log('🔄 Starting admin response polling...');
            console.log('   Polling every 1.5 seconds');
            console.log('   Session ID:', this.sessionId);
            
            // Poll immediately first
            this.checkAdminResponse();
            
            // Then poll every 1.5 seconds for up to 5 minutes (faster response)
            let elapsed = 0;
            const maxTime = 300000; // 5 minutes
            const interval = 1500; // 1.5 seconds (reduced for faster response)
            
            this.pollInterval = setInterval(async () => {
                elapsed += interval;
                
                console.log(`⏱️ Polling for admin response... (${elapsed / 1000}s)`);
                
                const gotResponse = await this.checkAdminResponse();
                
                if (gotResponse) {
                    console.log('✅ Admin response received!');
                    this.stopAdminResponsePolling();
                } else if (elapsed >= maxTime) {
                    console.log('⏰ Polling timeout reached');
                    this.stopAdminResponsePolling();
                    this.removeAdminWaitingIndicator();
                    this.appendMessage(
                        "Maaf, admin masih belum membalas. Anda boleh terus bertanya atau cuba lagi kemudian. 🙏",
                        'bot',
                        false,
                        { skipFeedback: true }
                    );
                }
            }, interval);
        }

        stopAdminResponsePolling() {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.pollInterval = null;
            }
            this.waitingForAdmin = false;
        }

        async checkAdminResponse() {
            try {
                if (!this.sessionId) {
                    console.error('❌ No session ID for polling');
                    return false;
                }
                
                const params = new URLSearchParams({ 
                    session_id: this.sessionId, 
                    _t: Date.now().toString() 
                });
                
                const url = `${this.apiBaseUrl}${window.CONFIG.ENDPOINTS.LIVE_CHAT_PENDING}?${params}`;
                console.log('   📡 Polling URL:', url);
                
                const res = await fetch(url, { 
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!res.ok) {
                    console.error('❌ Admin response check failed:', res.status, res.statusText);
                    return false;
                }
                
                const data = await res.json();
                console.log('   📥 Poll response:', data);
                
                if (data.success && data.pending && data.response?.admin_response) {
                    console.log('✅ ADMIN RESPONSE FOUND!');
                    console.log('   Admin:', data.response.admin_name);
                    console.log('   Response:', data.response.admin_response.substring(0, 50) + '...');
                    
                    // Remove waiting indicator
                    this.removeAdminWaitingIndicator();
                    
                    // Show admin response
                    const adminName = data.response.admin_name || 'Admin';
                    const adminResponse = data.response.admin_response;
                    
                    this.appendMessage(
                        `<div style="margin-bottom: 8px;"><strong>💬 Jawapan dari ${this.escapeHtml(adminName)}:</strong></div>${this.processLinks(adminResponse)}`,
                        'bot',
                        true,
                        { isAdminResponse: true, skipFeedback: true }
                    );
                    
                    return true;
                } else {
                    console.log('   ⏳ No admin response yet');
                    return false;
                }
                
            } catch (e) {
                console.error('❌ Polling error:', e);
                return false;
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
            // Stop any active polling
            this.stopAdminResponsePolling();
            this.removeAdminWaitingIndicator();
            
            // Stop any ongoing TTS
            if (this.voiceHandler) {
                this.voiceHandler.stopSpeaking();
            }
            
            this.messagesEl.innerHTML = '';
            this.sessionId = null;
            this.hasUserSentMessage = false;
            this.waitingForAdmin = false;

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
                    // Icon mapping for common questions
                    const iconMap = {
                        'perbezaan fakir': '📋',
                        'fakir dan miskin': '📋',
                        'fakir & miskin': '📋',
                        'kelayakan terima': '💰',
                        'terima zakat': '💰',
                        'ahli keluarga': '👥',
                        'keluarga': '👥',
                        'kalkulator': '🧮',
                        'kira zakat': '🧮',
                        'bayar zakat': '🌐',
                        'zakat online': '🌐',
                        'nisab': '📊',
                        'apa itu zakat': '❓',
                        'jenis zakat': '📚',
                        'default': '💡'
                    };

                    // Function to get icon based on question text
                    const getIcon = (question) => {
                        const lowerQuestion = question.toLowerCase();
                        for (const [key, icon] of Object.entries(iconMap)) {
                            if (lowerQuestion.includes(key)) {
                                return icon;
                            }
                        }
                        return iconMap.default;
                    };

                }
            } catch (e) {
                console.log('Could not load FAQs:', e);
            }
        }
    }

    window.ZakiaChatbot = ZakiaChatbot;
}

document.addEventListener('DOMContentLoaded', () => {
    // Create chatbot instance and expose it globally for FAQ browser
    console.log('📱 DOM loaded - Creating ZAKIA chatbot instance...');
    window.zakiaInstance = new ZakiaChatbot();
    window.chatbotInstance = window.zakiaInstance; // Alias for compatibility
    
    console.log('✅ ZAKIA Chatbot instance created and exposed globally');
});