/**
 * Zakat Calculator Handler for ZAKIA Chatbot
 * Manages interactive zakat calculation flow
 */

class ZakatHandler {
    constructor(chatbot) {
        this.chatbot = chatbot;
        this.state = {
            active: false,
            type: null,
            step: 0,
            data: {}
        };
        
        this.zakatTypes = {
            income: {
                name: 'Zakat Pendapatan',
                steps: ['amount', 'expenses'],
                prompts: {
                    amount: '💼 Sila masukkan jumlah pendapatan tahunan anda (RM):',
                    expenses: '💸 Sila masukkan jumlah perbelanjaan asas tahunan anda (RM):'
                }
            },
            savings: {
                name: 'Zakat Simpanan',
                steps: ['amount'],
                prompts: {
                    amount: '💰 Sila masukkan jumlah simpanan anda (RM):'
                }
            },
            gold: {
                name: 'Zakat Emas',
                steps: ['amount', 'gold_price'],
                prompts: {
                    amount: '⚱️ Sila masukkan berat emas anda (gram):',
                    gold_price: '💎 Sila masukkan harga emas semasa per gram (RM) atau tekan Enter untuk guna harga default (RM300/g):'
                }
            }
        };
    }

    /**
     * Detect if user wants to calculate zakat
     */
    detectZakatIntent(message) {
        const msg = message.toLowerCase();
        
        // Income zakat keywords
        if (msg.includes('kira zakat pendapatan') || 
            msg.includes('zakat pendapatan') || 
            msg.includes('zakat gaji') ||
            msg.includes('zakat income')) {
            return 'income';
        }
        
        // Savings zakat keywords
        if (msg.includes('kira zakat simpanan') || 
            msg.includes('zakat simpanan') || 
            msg.includes('zakat wang') ||
            msg.includes('zakat savings')) {
            return 'savings';
        }
        
        // Gold zakat keywords
        if (msg.includes('kira zakat emas') || 
            msg.includes('zakat emas') || 
            msg.includes('zakat gold')) {
            return 'gold';
        }
        
        // General zakat calculator request
        if ((msg.includes('kira zakat') || msg.includes('kalkulator zakat')) && 
            !this.state.active) {
            return 'menu';
        }
        
        // Nisab information request
        if (msg.includes('nisab') && !this.state.active) {
            return 'nisab';
        }
        
        return null;
    }

    /**
     * Show zakat type selection menu
     */
    showZakatMenu() {
        const menuHTML = `
            <div class="zakat-menu">
                <p style="margin-bottom: 12px;">Pilih jenis zakat yang ingin dikira:</p>
                <div class="zakat-buttons">
                    <button class="zakat-type-btn" data-type="income">
                        💼 Zakat Pendapatan
                    </button>
                    <button class="zakat-type-btn" data-type="savings">
                        💰 Zakat Simpanan
                    </button>
                    <button class="zakat-type-btn" data-type="gold">
                        ⚱️ Zakat Emas
                    </button>
                    <button class="zakat-type-btn" data-type="nisab">
                        📊 Maklumat Nisab
                    </button>
                </div>
            </div>
        `;
        
        this.chatbot.appendMessage(menuHTML, 'bot', true);
        this.attachMenuListeners();
    }

    /**
     * Attach event listeners to menu buttons
     */
    attachMenuListeners() {
        const buttons = document.querySelectorAll('.zakat-type-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.target.getAttribute('data-type');
                
                // Disable all buttons after selection
                buttons.forEach(b => b.disabled = true);
                e.target.classList.add('selected');
                
                if (type === 'nisab') {
                    this.fetchNisabInfo();
                } else {
                    this.startZakatCalculation(type);
                }
            });
        });
    }

    /**
     * Start zakat calculation process
     */
    startZakatCalculation(type) {
        this.state = {
            active: true,
            type: type,
            step: 0,
            data: {}
        };
        
        const config = this.zakatTypes[type];
        const firstStep = config.steps[0];
        const prompt = config.prompts[firstStep];
        
        setTimeout(() => {
            this.chatbot.appendMessage(prompt, 'bot');
        }, 500);
    }

    /**
     * Process user input during calculation
     */
    processInput(message) {
        if (!this.state.active) return false;
        
        const config = this.zakatTypes[this.state.type];
        const currentStepName = config.steps[this.state.step];
        
        // Validate and store input
        const value = this.validateInput(message, currentStepName);
        
        if (value === null) {
            this.chatbot.appendMessage(
                '❌ Nilai tidak sah. Sila masukkan nombor yang betul.',
                'bot'
            );
            return true;
        }
        
        this.state.data[currentStepName] = value;
        this.state.step++;
        
        // Check if we have all required inputs
        if (this.state.step >= config.steps.length) {
            this.calculateZakat();
            return true;
        }
        
        // Ask for next input
        const nextStep = config.steps[this.state.step];
        const nextPrompt = config.prompts[nextStep];
        
        setTimeout(() => {
            this.chatbot.appendMessage(nextPrompt, 'bot');
        }, 500);
        
        return true;
    }

    /**
     * Validate user input
     */
    validateInput(message, stepName) {
        // Remove RM, comma, and whitespace
        const cleaned = message.replace(/[RM,\s]/gi, '').trim();
        
        // For gold_price, allow empty (will use default)
        if (stepName === 'gold_price' && cleaned === '') {
            return null; // Will use default price
        }
        
        const number = parseFloat(cleaned);
        
        if (isNaN(number) || number < 0) {
            return null;
        }
        
        return number;
    }

    /**
     * Call API to calculate zakat
     */
    async calculateZakat() {
        this.chatbot.setTyping(true);
        
        try {
            const payload = {
                type: this.state.type,
                amount: this.state.data.amount
            };
            
            // Add type-specific data
            if (this.state.type === 'income') {
                payload.expenses = this.state.data.expenses;
            } else if (this.state.type === 'gold' && this.state.data.gold_price) {
                payload.gold_price = this.state.data.gold_price;
            }
            
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/calculate-zakat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Format and display result with animation
                this.displayResult(data.reply, data.data);
            } else {
                this.chatbot.appendMessage(
                    `❌ ${data.error || 'Ralat pengiraan. Sila cuba lagi.'}`,
                    'bot'
                );
            }
            
        } catch (error) {
            console.error('Zakat calculation error:', error);
            this.chatbot.appendMessage(
                '❌ Maaf, ralat sistem. Sila cuba lagi.',
                'bot'
            );
        } finally {
            this.chatbot.setTyping(false);
            this.resetState();
        }
    }

    /**
     * Display calculation result with animation
     */
    displayResult(message, data) {
        // Add result with special styling
        const resultHTML = `
            <div class="zakat-result">
                ${this.formatMessage(message)}
                ${data.reaches_nisab ? this.createPaymentButton(data) : ''}
            </div>
        `;
        
        setTimeout(() => {
            this.chatbot.appendMessage(resultHTML, 'bot', true);
            this.animateResult();
        }, 800);
    }

    /**
     * Format message with proper line breaks and styling
     */
    formatMessage(message) {
        return message
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/^(.+)$/gm, '<p>$1</p>');
    }

    /**
     * Create payment button for positive zakat amount
     */
    createPaymentButton(data) {
        if (!data.reaches_nisab || data.zakat_amount <= 0) return '';
        
        return `
            <div class="zakat-action" style="margin-top: 16px;">
                <button class="btn-pay-zakat" onclick="window.open('https://www.lznk.gov.my', '_blank')">
                    💳 Bayar Zakat Sekarang
                </button>
                <button class="btn-recalculate" onclick="window.zakatHandler.showZakatMenu()">
                    🔄 Kira Semula
                </button>
            </div>
        `;
    }

    /**
     * Animate result display
     */
    animateResult() {
        const results = document.querySelectorAll('.zakat-result');
        const lastResult = results[results.length - 1];
        
        if (lastResult) {
            lastResult.style.opacity = '0';
            lastResult.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                lastResult.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
                lastResult.style.opacity = '1';
                lastResult.style.transform = 'translateY(0)';
            }, 100);
        }
    }

    /**
     * Fetch nisab information
     */
    async fetchNisabInfo() {
        this.chatbot.setTyping(true);
        
        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/zakat/nisab-info`);
            const data = await response.json();
            
            if (data.success) {
                setTimeout(() => {
                    this.chatbot.appendMessage(this.formatMessage(data.reply), 'bot', true);
                }, 500);
            } else {
                this.chatbot.appendMessage('❌ Gagal mendapatkan maklumat nisab.', 'bot');
            }
            
        } catch (error) {
            console.error('Nisab info error:', error);
            this.chatbot.appendMessage('❌ Ralat sistem.', 'bot');
        } finally {
            this.chatbot.setTyping(false);
        }
    }

    /**
     * Reset calculation state
     */
    resetState() {
        this.state = {
            active: false,
            type: null,
            step: 0,
            data: {}
        };
    }

    /**
     * Cancel current calculation
     */
    cancel() {
        if (this.state.active) {
            this.chatbot.appendMessage(
                '❌ Pengiraan zakat dibatalkan. Taip "kira zakat" untuk cuba lagi.',
                'bot'
            );
            this.resetState();
        }
    }
}

// Export for use in main chatbot
window.ZakatHandler = ZakatHandler;