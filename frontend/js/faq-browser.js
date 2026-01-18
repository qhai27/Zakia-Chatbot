// =========================
// FAQ BROWSER HANDLER
// =========================

class FAQBrowser {
    constructor() {
        this.modal = null;
        this.content = null;
        this.searchInput = null;
        this.closeBtn = null;
        this.overlay = null;
        
        this.faqs = [];
        this.categories = [];
        this.filteredFaqs = [];
        
        this.apiBaseUrl = window.CONFIG?.API_BASE_URL || 'http://127.0.0.1:5000';
        
        this.init();
    }
    
    init() {
        // Get DOM elements
        this.modal = document.getElementById('faqBrowserModal');
        this.content = document.getElementById('faqBrowserContent');
        this.searchInput = document.getElementById('faqSearchInput');
        this.closeBtn = this.modal?.querySelector('.faq-modal-close');
        this.overlay = this.modal?.querySelector('.faq-modal-overlay');
        
        if (!this.modal || !this.content) {
            console.error('FAQ Browser: Modal elements not found');
            return;
        }
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('✅ FAQ Browser initialized');
    }
    
    setupEventListeners() {
        // Close button
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.hide());
        }
        
        // Overlay click
        if (this.overlay) {
            this.overlay.addEventListener('click', () => this.hide());
        }
        
        // Search input
        if (this.searchInput) {
            let searchTimeout;
            this.searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.filterFAQs(e.target.value);
                }, 300);
            });
        }
        
        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal?.style.display === 'flex') {
                this.hide();
            }
        });
    }
    
    async show() {
        if (!this.modal) return;
        
        // Show modal
        this.modal.style.display = 'flex';
        
        // Focus search input
        if (this.searchInput) {
            this.searchInput.value = '';
            setTimeout(() => this.searchInput.focus(), 100);
        }
        
        // Load FAQs if not already loaded
        if (this.faqs.length === 0) {
            await this.loadFAQs();
        } else {
            this.renderFAQs(this.faqs);
        }
    }
    
    hide() {
        if (this.modal) {
            this.modal.style.display = 'none';
        }
        
        // Clear search
        if (this.searchInput) {
            this.searchInput.value = '';
        }
    }
    
    async loadFAQs() {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.apiBaseUrl}/faqs`);
            const data = await response.json();
            
            if (data.success && data.faqs) {
                this.faqs = data.faqs;
                this.extractCategories();
                this.renderFAQs(this.faqs);
                
                console.log(`✅ Loaded ${this.faqs.length} FAQs`);
            } else {
                this.showError('Gagal memuatkan soalan');
            }
            
        } catch (error) {
            console.error('FAQ load error:', error);
            this.showError('Ralat sambungan. Sila cuba lagi.');
        }
    }
    
    extractCategories() {
        const categorySet = new Set();
        
        this.faqs.forEach(faq => {
            const category = faq.category || 'Umum';
            categorySet.add(category);
        });
        
        this.categories = Array.from(categorySet).sort((a, b) => {
            // Put "Umum" first
            if (a === 'Umum') return -1;
            if (b === 'Umum') return 1;
            return a.localeCompare(b);
        });
    }
    
    filterFAQs(searchTerm) {
        if (!searchTerm || searchTerm.trim() === '') {
            this.renderFAQs(this.faqs);
            return;
        }
        
        const term = searchTerm.toLowerCase().trim();
        
        const filtered = this.faqs.filter(faq => {
            const question = (faq.question || '').toLowerCase();
            const answer = (faq.answer || '').toLowerCase();
            const category = (faq.category || '').toLowerCase();
            
            return question.includes(term) || 
                   answer.includes(term) || 
                   category.includes(term);
        });
        
        this.renderFAQs(filtered);
    }
    
    renderFAQs(faqs) {
        if (!this.content) return;
        
        if (faqs.length === 0) {
            this.content.innerHTML = `
                <div class="faq-empty">
                    <p>😔 Tiada soalan dijumpai</p>
                    <small>Cuba cari dengan kata kunci lain</small>
                </div>
            `;
            return;
        }
        
        // Group FAQs by category
        const grouped = {};
        
        faqs.forEach(faq => {
            const category = faq.category || 'Umum';
            if (!grouped[category]) {
                grouped[category] = [];
            }
            grouped[category].push(faq);
        });
        
        // Sort categories
        const sortedCategories = Object.keys(grouped).sort((a, b) => {
            if (a === 'Umum') return -1;
            if (b === 'Umum') return 1;
            return a.localeCompare(b);
        });
        
        // Build HTML
        let html = '';
        
        sortedCategories.forEach(category => {
            const categoryFaqs = grouped[category];
            const categoryIcon = this.getCategoryIcon(category);
            
            html += `
                <div class="faq-category-section">
                    <div class="faq-category-header">
                        <span class="faq-category-icon">${categoryIcon}</span>
                        <h4 class="faq-category-title">${this.escapeHtml(category)}</h4>
                        <span class="faq-category-count">${categoryFaqs.length}</span>
                    </div>
                    <div class="faq-list">
            `;
            
            categoryFaqs.forEach(faq => {
                html += `
                    <div class="faq-item" data-faq-id="${faq.id_faq}">
                        <div class="faq-question">
                            <span class="faq-q-icon">❓</span>
                            <span class="faq-q-text">${this.escapeHtml(faq.question)}</span>
                        </div>
                        <button class="faq-select-btn" data-faq-id="${faq.id_faq}">
                            Pilih ›
                        </button>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        this.content.innerHTML = html;
        
        // Attach click handlers
        this.attachFAQClickHandlers();
    }
    
    attachFAQClickHandlers() {
        const buttons = this.content.querySelectorAll('.faq-select-btn');
        
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const faqId = parseInt(btn.getAttribute('data-faq-id'));
                this.selectFAQ(faqId);
            });
        });
        
        // Also make the entire FAQ item clickable
        const items = this.content.querySelectorAll('.faq-item');
        items.forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.classList.contains('faq-select-btn')) return;
                
                const faqId = parseInt(item.getAttribute('data-faq-id'));
                this.selectFAQ(faqId);
            });
        });
    }
    
    selectFAQ(faqId) {
        const faq = this.faqs.find(f => f.id_faq === faqId);
        
        if (!faq) {
            console.error('FAQ not found:', faqId);
            return;
        }
        
        console.log('📌 Selected FAQ:', faq.question);
        
        // Hide modal
        this.hide();
        
        // Send FAQ question to chatbot
        if (window.ZakiaChatbot) {
            // Use the chatbot instance to send the message
            const chatbot = window.zakiaInstance || window.chatbotInstance;
            if (chatbot && typeof chatbot.sendMessage === 'function') {
                // Add user message to chat
                chatbot.appendMessage(faq.question, 'user');
                
                // Show typing indicator
                chatbot.setTyping(true);
                
                // Send to backend and get response
                setTimeout(async () => {
                    try {
                        const response = await fetch(`${this.apiBaseUrl}/chat`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                message: faq.question,
                                session_id: chatbot.sessionId
                            })
                        });
                        
                        const data = await response.json();
                        
                        // Hide typing
                        chatbot.setTyping(false);
                        
                        // Show bot response
                        chatbot.appendMessage(data.reply || faq.answer, 'bot');
                        
                        // Update session ID
                        if (data.session_id) {
                            chatbot.sessionId = data.session_id;
                        }
                        
                    } catch (error) {
                        console.error('Chat error:', error);
                        chatbot.setTyping(false);
                        chatbot.appendMessage('Maaf, ralat berlaku. Sila cuba lagi. 😅', 'bot');
                    }
                }, 500);
            } else {
                // Fallback: Use input field
                const inputEl = document.getElementById('userInput');
                const sendBtn = document.getElementById('sendBtn');
                
                if (inputEl && sendBtn) {
                    inputEl.value = faq.question;
                    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                    sendBtn.click();
                }
            }
        }
    }
    
    getCategoryIcon(category) {
        const iconMap = {
            'Umum': '📌',
            'Pembayaran': '💳',
            'Nisab': '📊',
            'Kadar': '💰',
            'Perniagaan': '🏪',
            'Haul': '📅',
            'LZNK': '🏢',
            'Zakat Fitrah': '🌙',
            'Zakat Pendapatan': '💵',
            'Zakat Emas': '👑',
            'Zakat Saham': '📈'
        };
        
        return iconMap[category] || '📚';
    }
    
    showLoading() {
        if (this.content) {
            this.content.innerHTML = `
                <div class="faq-loading">
                    <div class="faq-spinner"></div>
                    <p>Memuat soalan...</p>
                </div>
            `;
        }
    }
    
    showError(message) {
        if (this.content) {
            this.content.innerHTML = `
                <div class="faq-error">
                    <p>❌ ${this.escapeHtml(message)}</p>
                    <button class="faq-retry-btn" onclick="window.FAQBrowser.loadFAQs()">
                        🔄 Cuba Lagi
                    </button>
                </div>
            `;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
}

// Initialize FAQ Browser when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.FAQBrowser = new FAQBrowser();
    console.log('✅ FAQ Browser ready');
});