/**
 * Reminder Flow Handler for Zakat Calculator
 * Manages step-by-step reminder opt-in process
 */

class ReminderHandler {
    constructor(chatbot) {
        this.chatbot = chatbot;
        this.state = {
            active: false,
            step: 0, // 0: ask permission, 1: name, 2: ic, 3: phone
            data: {
                name: null,
                ic_number: null,
                phone: null,
                zakat_type: null,
                zakat_amount: null
            }
        };
        
        this.steps = {
            0: 'permission',
            1: 'name',
            2: 'ic',
            3: 'phone'
        };
        
        this.prompts = {
            permission: 'Adakah anda ingin menerima peringatan pembayaran zakat?',
            name: 'Baik, boleh saya tahu nama penuh anda? 📝',
            ic: (name) => `Terima kasih ${name} 😊. Seterusnya, sila masukkan nombor IC anda (tanpa tanda sempang).`,
            phone: 'Baik, terakhir sekali, sila masukkan nombor telefon anda. 📱'
        };
    }

    /**
     * Start reminder collection flow
     */
    startReminderFlow(zakatType, zakatAmount) {
        this.state = {
            active: true,
            step: 0,
            data: {
                name: null,
                ic_number: null,
                phone: null,
                zakat_type: zakatType,
                zakat_amount: zakatAmount
            }
        };
        
        // Show permission buttons
        setTimeout(() => {
            this.showPermissionPrompt();
        }, 500);
    }

    /**
     * Show permission prompt with Yes/No buttons
     */
    showPermissionPrompt() {
        const html = `
            <div class="reminder-prompt">
                <p style="margin-bottom: 16px; font-weight: 600;">
                    ${this.prompts.permission}
                </p>
                <div class="reminder-buttons">
                    <button class="reminder-btn yes-btn" data-answer="yes">
                        ✅ Ya, saya mahu peringatan
                    </button>
                    <button class="reminder-btn no-btn" data-answer="no">
                        ❌ Tidak, terima kasih
                    </button>
                </div>
            </div>
        `;
        
        this.chatbot.appendMessage(html, 'bot', true);
        this.attachPermissionListeners();
    }

    /**
     * Attach event listeners to permission buttons
     */
    attachPermissionListeners() {
        const buttons = document.querySelectorAll('.reminder-btn');
        
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const answer = e.target.getAttribute('data-answer');
                
                // Disable all buttons
                buttons.forEach(b => b.disabled = true);
                e.target.classList.add('selected');
                
                if (answer === 'yes') {
                    this.state.step = 1; // Move to name step
                    setTimeout(() => {
                        this.askName();
                    }, 500);
                } else {
                    this.chatbot.appendMessage(
                        'Baik, semoga Allah memberkati rezeki anda. 🤲',
                        'bot'
                    );
                    this.resetState();
                }
            });
        });
    }

    /**
     * Ask for user's name
     */
    askName() {
        this.chatbot.appendMessage(this.prompts.name, 'bot');
    }

    /**
     * Ask for user's IC number
     */
    askIC() {
        const firstName = this.state.data.name.split(' ')[0];
        const prompt = this.prompts.ic(firstName);
        this.chatbot.appendMessage(prompt, 'bot');
    }

    /**
     * Ask for user's phone number
     */
    askPhone() {
        this.chatbot.appendMessage(this.prompts.phone, 'bot');
    }

    /**
     * Process user input during reminder flow
     */
    async processInput(message) {
        // Debug: log incoming message and state
        try { console.debug('ReminderHandler.processInput', { message, state: this.state }); } catch (_) {}

        // If reminder flow not active or not waiting for input, do nothing
        if (!this.state || !this.state.active || !this.state.waitingFor) return false;

        const text = (message || '').trim();
        if (!text) {
            this.chatbot.appendMessage('Sila masukkan nilai yang sah.', 'bot');
            return true;
        }

        try {
            // ensure data object exists
            if (!this.state.data) this.state.data = {};

            const field = this.state.waitingFor;

            if (field === 'name') {
                if (text.length < 3) {
                    this.chatbot.appendMessage('Sila masukkan nama penuh yang sah (sekurang-kurangnya 3 aksara).', 'bot');
                    return true;
                }
                // save name and move to IC step
                this.state.data.name = text;
                // clear waitingFor before asking next so double messages are ignored
                this.state.waitingFor = null;
                // prompt next
                this.askIC();
                return true;
            }

            if (field === 'ic') {
                const clean = text.replace(/[-\s]/g, '');
                if (!/^\d{12}$/.test(clean)) {
                    this.chatbot.appendMessage('Nombor IC tidak sah. Sila masukkan 12 digit tanpa tanda sempang.', 'bot');
                    return true;
                }
                this.state.data.ic_number = clean;
                this.state.waitingFor = null;
                this.askPhone();
                return true;
            }

            if (field === 'phone') {
                let phone = text.replace(/[\s\-]/g, '');
                if (phone.startsWith('+')) phone = phone.replace('+', '');
                if (!/^\d{9,13}$/.test(phone)) {
                    this.chatbot.appendMessage('Nombor telefon tidak sah. Sila cuba lagi.', 'bot');
                    return true;
                }
                if (phone.startsWith('60') && phone.length >= 11) phone = '0' + phone.slice(2);
                this.state.data.phone = phone;
                this.state.waitingFor = null;
                // all data collected -> submit
                await this._submitReminder();
                return true;
            }

            // If waitingFor set but field not matched, consume message to avoid other handlers interfering
            return true;
        } catch (err) {
            console.error('ReminderHandler.processInput error', err);
            this.chatbot.appendMessage('Maaf, ralat berlaku semasa memproses input. Sila cuba lagi.', 'bot');
            this.resetState();
            return true;
        }
    }

    /**
     * Save reminder to database
     */
    async saveReminder() {
        this.chatbot.setTyping(true);
        
        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/save-reminder`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: this.state.data.name,
                    ic_number: this.state.data.ic_number,
                    phone: this.state.data.phone,
                    zakat_type: this.state.data.zakat_type,
                    zakat_amount: this.state.data.zakat_amount
                })
            });
            
            const data = await response.json();
            
            setTimeout(() => {
                this.chatbot.setTyping(false);
                
                if (data.success) {
                    // Success message
                    this.chatbot.appendMessage(data.reply, 'bot');
                } else {
                    // Error message
                    this.chatbot.appendMessage(
                        `❌ ${data.error || 'Ralat menyimpan maklumat. Sila cuba lagi.'}`,
                        'bot'
                    );
                }
                
                this.resetState();
            }, 800);
            
        } catch (error) {
            console.error('Error saving reminder:', error);
            this.chatbot.setTyping(false);
            this.chatbot.appendMessage(
                '❌ Maaf, sistem ralat. Sila cuba lagi kemudian.',
                'bot'
            );
            this.resetState();
        }
    }

    /**
     * Reset reminder state
     */
    resetState() {
        this.state = {
            active: false,
            step: 0,
            data: {
                name: null,
                ic_number: null,
                phone: null,
                zakat_type: null,
                zakat_amount: null
            }
        };
    }

    /**
     * Check if handler is currently active
     */
    isActive() {
        return this.state.active;
    }

    /**
     * Get current step name
     */
    getCurrentStep() {
        return this.steps[this.state.step];
    }

    /**
     * Cancel reminder flow
     */
    cancel() {
        if (this.state.active) {
            this.chatbot.appendMessage(
                '❌ Pendaftaran peringatan dibatalkan.',
                'bot'
            );
            this.resetState();
        }
    }
}

// Export for use in main chatbot
window.ReminderHandler = ReminderHandler;