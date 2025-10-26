
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

    appendMessage(text, sender) {
        const msg = document.createElement('div');
        msg.className = `msg ${sender}`;

        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });

        if (sender === 'bot') {
            msg.innerHTML = `
                <img src="zakia-avatar.png" class="msg-avatar" alt="ZAKIA">
                <div class="bubble-container">
                    <div class="bubble bot-bubble">${this.escapeHtml(text)}</div>
                    <div class="msg-time">${timeString}</div>
                </div>
            `;
        } else {
            msg.innerHTML = `
                <div class="bubble-container">
                    <div class="bubble user-bubble">${this.escapeHtml(text)}</div>
                    <div class="msg-time">${timeString}</div>
                </div>
            `;
        }

        this.messagesEl.appendChild(msg);
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
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