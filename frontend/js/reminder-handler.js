/**
 * Reminder Flow Handler for Zakat Calculator
 * Manages step-by-step reminder opt-in process
 */

class ReminderHandler {
    constructor(chatbot) {
        this.chatbot = chatbot;
        this.state = {
            active: false,
            waitingFor: null,
            data: {
                name: null,
                ic_number: null,
                phone: null,
                zakat_type: null,
                zakat_amount: null
            }
        };
        
        this.prompts = {
            permission: 'Adakah anda ingin menerima peringatan pembayaran zakat? 🔔',
            name: 'Baik, boleh saya tahu nama penuh anda? 📝',
            ic: (name) => {
                const firstName = (name || '').split(' ')[0] || '';
                return `Terima kasih ${firstName} 😊. Seterusnya, sila masukkan nombor IC anda (12 digit tanpa tanda sempang, contoh: 950101015678).`;
            },
            phone: 'Baik, terakhir sekali, sila masukkan nombor telefon anda tanpa sebarang ruang atau tanda sempang (contoh: 0123456789). 📱'
        };
    }

    /**
     * Start reminder collection flow
     */
    startReminderFlow(zakatType, zakatAmount) {
        this.state = {
            active: true,
            waitingFor: null,
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
                <p style="margin-bottom: 16px; font-weight: 600; color: #2d3748;">
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
            if (btn.dataset._reminderAttached) return;
            btn.dataset._reminderAttached = '1';
            
            btn.addEventListener('click', (e) => {
                const answer = e.target.getAttribute('data-answer');
                
                // Disable all buttons
                buttons.forEach(b => b.disabled = true);
                e.target.classList.add('selected');
                
                if (answer === 'yes') {
                    setTimeout(() => {
                        this.askName();
                    }, 500);
                } else {
                    setTimeout(() => {
                        this.chatbot.appendMessage(
                            'Baik, terima kasih. Semoga Allah memberkati rezeki anda. 🤲',
                            'bot'
                        );
                        this.resetState();
                    }, 500);
                }
            });
        });
    }
    
    /**
     * Ask for user's name
     */
    askName() {
        this.state.waitingFor = 'name';
        this.chatbot.appendMessage(this.prompts.name, 'bot');
    }

    /**
     * Ask for user's IC number
     */
    askIC() {
        const firstName = (this.state.data.name || '').split(' ')[0] || '';
        const prompt = this.prompts.ic(firstName);
        this.state.waitingFor = 'ic';
        this.chatbot.appendMessage(prompt, 'bot');
    }

    /**
     * Ask for user's phone number
     */
    askPhone() {
        this.state.waitingFor = 'phone';
        this.chatbot.appendMessage(this.prompts.phone, 'bot');
    }

    /**
     * Process user input during reminder flow
     */
    async processInput(message) {
        // If reminder flow not active or not waiting for input, ignore
        if (!this.state || !this.state.active || !this.state.waitingFor) {
            return false;
        }

        const text = (message || '').trim();
        
        // Check for cancel command
        if (text.toLowerCase().includes('batal') || text.toLowerCase().includes('cancel')) {
            this.cancel();
            return true;
        }
        
        if (!text) {
            this.chatbot.appendMessage('Sila masukkan nilai yang sah. ⚠️', 'bot');
            return true;
        }

        try {
            const field = this.state.waitingFor;

            if (field === 'name') {
                if (text.length < 3) {
                    this.chatbot.appendMessage(
                        'Sila masukkan nama penuh yang sah (sekurang-kurangnya 3 aksara). ⚠️',
                        'bot'
                    );
                    return true;
                }
                
                // Save name and move to IC step
                this.state.data.name = text;
                this.state.waitingFor = null;
                
                setTimeout(() => {
                    this.askIC();
                }, 500);
                return true;
            }

            if (field === 'ic') {
                const clean = text.replace(/[-\s]/g, '');
                
                if (!/^\d{12}$/.test(clean)) {
                    this.chatbot.appendMessage(
                        'Nombor IC tidak sah. Sila masukkan 12 digit tanpa tanda sempang (contoh: 950101015678). ⚠️',
                        'bot'
                    );
                    return true;
                }
                
                // Save IC and move to phone step
                this.state.data.ic_number = clean;
                this.state.waitingFor = null;
                
                setTimeout(() => {
                    this.askPhone();
                }, 500);
                return true;
            }

            if (field === 'phone') {
                let phone = text.replace(/[\s\-]/g, '');
                
                // Handle +60 format
                if (phone.startsWith('+60')) {
                    phone = '0' + phone.slice(3);
                } else if (phone.startsWith('60') && phone.length >= 11) {
                    phone = '0' + phone.slice(2);
                }
                
                // Validate phone (10-11 digits starting with 0)
                if (!/^0\d{9,10}$/.test(phone)) {
                    this.chatbot.appendMessage(
                        'Nombor telefon tidak sah. Sila masukkan nombor telefon Malaysia yang betul (contoh: 0123456789). ⚠️',
                        'bot'
                    );
                    return true;
                }
                
                // Save phone and submit
                this.state.data.phone = phone;
                this.state.waitingFor = null;
                
                await this.submitReminder();
                return true;
            }

            return true;
        } catch (err) {
            console.error('ReminderHandler.processInput error', err);
            this.chatbot.appendMessage(
                '❌ Maaf, ralat berlaku semasa memproses input. Sila cuba lagi.',
                'bot'
            );
            this.resetState();
            return true;
        }
    }

    /**
     * Submit reminder to backend
     */
    async submitReminder() {
        this.chatbot.setTyping(true);
        
        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/api/save-reminder`, {
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
                    const firstName = (this.state.data.name || '').split(' ')[0] || 'Pengguna';
                    this.chatbot.appendMessage(
                        `✅ Terima kasih ${firstName}! Maklumat peringatan anda telah berjaya disimpan. LZNK akan menghantar peringatan zakat kepada anda nanti. 🤲\n\nSemoga Allah memberkati rezeki anda. 🌟`,
                        'bot'
                    );
                } else {
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
            waitingFor: null,
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
        return this.state && this.state.active;
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