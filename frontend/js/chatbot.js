
class ZakiaChatbot {
    constructor() {
        this.messagesEl = document.getElementById("messages");
        this.inputEl = document.getElementById("userInput");
        this.typingEl = document.getElementById("typing");
        this.sendBtn = document.getElementById("sendBtn");
        this.endBtn = document.getElementById("endChat");
        this.quickRepliesEl = document.getElementById("quickReplies");
        this.minimizeBtn = document.querySelector('.minimize-btn'); // Add this line
        this.chatbox = document.querySelector('.chatbox'); // Add this line

        this.sessionId = null;
        this.hasUserSentMessage = false;
        this.apiBaseUrl = window.CONFIG.API_BASE_URL;
        this.isMinimized = false; // Add this line

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadFAQs();
    }

    setupEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        this.quickRepliesEl.addEventListener('click', (e) => {
            const target = e.target;
            if (target.classList.contains('quick-reply')) {
                this.handleQuickReplyClick(target);
            }
        });

        this.endBtn.addEventListener('click', () => this.endChat());
        
        // Add minimize button event listener
        this.minimizeBtn.addEventListener('click', () => this.toggleMinimize());
    }

    // Add this new method
    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        
        if (this.isMinimized) {
            // Hide the chatbox
            this.chatbox.style.display = 'none';
            
            // Create minimized widget if it doesn't exist
            if (!document.getElementById('chatWidget')) {
                this.createMinimizedWidget();
            }
        } else {
            // Show the chatbox
            this.chatbox.style.display = 'flex';
            
            // Remove minimized widget
            const widget = document.getElementById('chatWidget');
            if (widget) {
                widget.remove();
            }
        }
    }

    // Add this new method to create the minimized widget
    createMinimizedWidget() {
        const widget = document.createElement('div');
        widget.id = 'chatWidget';
        widget.innerHTML = `
            <img src="zakia-avatar.png" alt="ZAKIA" class="widget-avatar">
            <div class="widget-content">
                <div class="widget-title">ZAKIA</div>
                <div class="widget-subtitle">Chat dengan kami</div>
            </div>
        `;
        
        // Add click event to restore chatbox
        const self = this;
        widget.addEventListener('click', function() {
            self.isMinimized = false;
            self.chatbox.style.display = 'flex';
            widget.remove();
        });
        
        document.body.appendChild(widget);
    }

    // Replace the appendMessage method in frontend/js/chatbot.js

appendMessage(text, sender) {
    const msg = document.createElement('div');
    msg.className = `msg ${sender}`;

    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });

    // Process text to make links clickable
    const processedText = this.processLinks(text);

    if (sender === 'bot') {
        msg.innerHTML = `
            <img src="zakia-avatar.png" class="msg-avatar" alt="ZAKIA">
            <div class="bubble-container">
                <div class="bubble bot-bubble">${processedText}</div>
                <div class="msg-time">${timeString}</div>
            </div>
        `;
    } else {
        msg.innerHTML = `
            <div class="bubble-container">
                <div class="bubble user-bubble">${processedText}</div>
                <div class="msg-time">${timeString}</div>
            </div>
        `;
    }

    this.messagesEl.appendChild(msg);
    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
}

// Add this new method to the ZakiaChatbot class
processLinks(text) {
    // First, escape HTML to prevent XSS attacks
    let processed = this.escapeHtml(text);
    
    // Pattern 1: Match HTML anchor tags that are already in the text
    // (from admin panel where users can insert <a> tags)
    const htmlLinkPattern = /&lt;a\s+href=&quot;([^&]+)&quot;[^&]*&gt;([^&]+)&lt;\/a&gt;/gi;
    processed = processed.replace(htmlLinkPattern, (match, url, label) => {
        // Unescape the URL and label
        const cleanUrl = url.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"');
        const cleanLabel = label.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
        return `<a href="${cleanUrl}" target="_blank" rel="noopener noreferrer" class="chat-link">${cleanLabel}</a>`;
    });
    
    // Pattern 2: Auto-detect URLs in plain text and make them clickable
    const urlPattern = /(https?:\/\/[^\s<>"]+[^\s<>".,;:!?)])/gi;
    processed = processed.replace(urlPattern, (url) => {
        // Extract domain for display (optional - you can show full URL)
        const displayUrl = url.length > 50 ? url.substring(0, 47) + '...' : url;
        return `<a href="${url}" target="_blank" rel="noopener noreferrer" class="chat-link">${displayUrl}</a>`;
    });
    
    // Pattern 3: Detect phone numbers and make them callable
    const phonePattern = /(\+?[\d\s\-()]{10,})/g;
    processed = processed.replace(phonePattern, (phone) => {
        const cleanPhone = phone.replace(/[\s\-()]/g, '');
        if (cleanPhone.length >= 10) {
            return `<a href="tel:${cleanPhone}" class="chat-link">${phone}</a>`;
        }
        return phone;
    });
    
    // Pattern 4: Detect email addresses
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
        this.setTyping(true);
        this.hideQuickReplies();

        this.hasUserSentMessage = true;

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

            this.appendMessage(data.reply || window.CONFIG.MESSAGES.SERVER_ERROR, 'bot');

            if (!this.hasUserSentMessage) {
                setTimeout(() => this.showQuickReplies(), window.CONFIG.UI.TYPING_DELAY);
            }

        } catch (e) {
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
        this.messagesEl.innerHTML = '';
        this.sessionId = null;
        this.hasUserSentMessage = false;
        this.appendMessage(window.CONFIG.MESSAGES.SESSION_ENDED, 'bot');
        this.showQuickReplies();
    }

    async loadFAQs() {
        try {
            const res = await fetch(`${this.apiBaseUrl}${window.CONFIG.ENDPOINTS.FAQS}`);
            const data = await res.json();

            if (data.faqs && data.faqs.length > 0) {
                const quickReplies = data.faqs.slice(0, window.CONFIG.UI.MAX_QUICK_REPLIES);
                this.quickRepliesEl.innerHTML = quickReplies.map(faq =>
                    `<button class="quick-reply" data-text="${this.escapeHtml(faq.question)}">${this.escapeHtml(faq.question)}</button>`
                ).join('');
            }
        } catch (e) {
            console.log('Could not load FAQs:', e);
        }
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ZakiaChatbot();
});