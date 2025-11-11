/**
 * Updated ZakatHandler with Reminder Integration
 * Manages zakat calculation and reminder opt-in flow
 */

class ZakatHandler {
    constructor(chatbot) {
        this.chatbot = chatbot;
        this.state = {
            active: false,
            type: null,
            step: 0,
            data: {},
            yearType: null,
            year: null,
            availableYears: []
        };
        
        // Initialize reminder handler
        this.reminderHandler = new window.ReminderHandler(chatbot);
        
        this.zakatTypes = {
            income: {
                name: 'Zakat Pendapatan',
                icon: '💼',
                steps: ['year_type', 'year', 'amount', 'expenses'],
                prompts: {
                    year_type: 'Sila pilih jenis tahun:',
                    year: 'Sila pilih tahun:',
                    amount: '💼 Sila masukkan jumlah pendapatan tahunan anda (RM):',
                    expenses: '💸 Sila masukkan jumlah perbelanjaan asas tahunan anda (RM):'
                }
            },
            savings: {
                name: 'Zakat Simpanan',
                icon: '💰',
                steps: ['year_type', 'year', 'amount'],
                prompts: {
                    year_type: 'Sila pilih jenis tahun:',
                    year: 'Sila pilih tahun:',
                    amount: '💰 Sila masukkan jumlah simpanan anda (RM):'
                }
            }
        };
    }

    detectZakatIntent(message) {
        const msg = message.toLowerCase();
        
        if (msg.includes('kira zakat pendapatan') || 
            msg.includes('zakat pendapatan') || 
            msg.includes('zakat gaji') ||
            msg.includes('zakat income')) {
            return 'income';
        }
        
        if (msg.includes('kira zakat simpanan') || 
            msg.includes('zakat simpanan') || 
            msg.includes('zakat wang') ||
            msg.includes('zakat savings')) {
            return 'savings';
        }
        
        if ((msg.includes('kira zakat') || msg.includes('kalkulator zakat')) && 
            !this.state.active) {
            return 'menu';
        }
        
        if (msg.includes('nisab') && !this.state.active) {
            return 'nisab';
        }
        
        return null;
    }

    showZakatMenu() {
        const menuHTML = `
            <div class="zakat-menu">
                <p style="margin-bottom: 16px; font-weight: 600;">💰 Pilih jenis zakat yang ingin dikira:</p>
                <div class="zakat-buttons">
                    <button class="zakat-type-btn" data-type="income">
                        💼 Zakat Pendapatan
                    </button>
                    <button class="zakat-type-btn" data-type="savings">
                        💰 Zakat Simpanan
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

    attachMenuListeners() {
        const buttons = document.querySelectorAll('.zakat-type-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const type = e.target.getAttribute('data-type');
                buttons.forEach(b => b.disabled = true);
                e.target.classList.add('selected');
                
                if (type === 'nisab') {
                    this.showNisabYearSelection();
                } else {
                    this.startZakatCalculation(type);
                }
            });
        });
    }

    startZakatCalculation(type) {
        this.state = {
            active: true,
            type: type,
            step: 0,
            data: {},
            yearType: null,
            year: null,
            availableYears: []
        };
        
        setTimeout(() => {
            this.showYearTypeSelection();
        }, 500);
    }

    showYearTypeSelection() {
        const config = this.zakatTypes[this.state.type];
        const html = `
            <div class="zakat-year-selection">
                <p style="margin-bottom: 12px; font-weight: 600;">📅 ${config.prompts.year_type}</p>
                <div class="zakat-buttons">
                    <button class="zakat-year-type-btn" data-year-type="H">
                        🌙 Tahun Hijrah
                    </button>
                    <button class="zakat-year-type-btn" data-year-type="M">
                        📆 Tahun Masihi
                    </button>
                    <button class="zakat-cancel-btn">
                        ❌ Batal
                    </button>
                </div>
            </div>
        `;
        
        this.chatbot.appendMessage(html, 'bot', true);
        this.attachYearTypeListeners();
    }

    attachYearTypeListeners() {
        const buttons = document.querySelectorAll('.zakat-year-type-btn');
        const cancelBtns = document.querySelectorAll('.zakat-cancel-btn');
        
        buttons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const yearType = e.target.getAttribute('data-year-type');
                buttons.forEach(b => b.disabled = true);
                cancelBtns.forEach(cb => cb.disabled = true);
                e.target.classList.add('selected');
                
                this.state.yearType = yearType;
                await this.fetchAndShowYears(yearType);
            });
        });
        
        cancelBtns.forEach(btn => {
            if (!btn.dataset.zakatCancelAttached) {
                btn.addEventListener('click', () => this.cancel());
                btn.dataset.zakatCancelAttached = '1';
            }
        });
    }

    async fetchAndShowYears(yearType) {
        this.chatbot.setTyping(true);
        
        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/zakat/years?type=${yearType}`);
            const data = await response.json();
            
            if (data.success && data.years && Array.isArray(data.years)) {
                this.state.availableYears = data.years;
                setTimeout(() => {
                    this.chatbot.setTyping(false);
                    this.showYearSelection(data.years, yearType);
                }, 500);
            } else {
                throw new Error('Gagal mendapatkan senarai tahun');
            }
        } catch (error) {
            console.error('Error fetching years:', error);
            this.chatbot.setTyping(false);
            
            const defaultYears = yearType === 'H' 
                ? ['1448','1447', '1446', '1445'] 
                : ['2025', '2024', '2023', '2022'];
            
            this.chatbot.appendMessage('ℹ️ Menggunakan tahun tersedia...', 'bot');
            setTimeout(() => {
                this.showYearSelection(defaultYears, yearType);
            }, 300);
        }
    }

    showYearSelection(years, yearType) {
        const config = this.zakatTypes[this.state.type];
        const yearLabel = yearType === 'H' ? 'Hijrah' : 'Masihi';
        const displayYears = Array.isArray(years) ? years.slice(0, 5) : [];
        
        if (displayYears.length === 0) {
            displayYears.push(...(yearType === 'H' 
                ? ['1448', '1447', '1446'] 
                : ['2025', '2024', '2023']));
        }
        
        const yearButtons = displayYears.map(year => 
            `<button class="zakat-year-btn" data-year="${year}">${year} ${yearLabel}</button>`
        ).join('');
        
        const html = `
            <div class="zakat-year-list">
                <p style="margin-bottom: 12px; font-weight: 600;">📅 ${config.prompts.year}</p>
                <div class="zakat-buttons">
                    ${yearButtons}
                    <button class="zakat-cancel-btn">❌ Batal</button>
                </div>
            </div>
        `;
        
        this.chatbot.appendMessage(html, 'bot', true);
        this.attachYearListeners();
    }

    attachYearListeners() {
        const buttons = document.querySelectorAll('.zakat-year-btn');
        const cancelBtns = document.querySelectorAll('.zakat-cancel-btn');
        
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const year = e.target.getAttribute('data-year');
                buttons.forEach(b => b.disabled = true);
                cancelBtns.forEach(cb => cb.disabled = true);
                e.target.classList.add('selected');
                
                this.state.year = year;
                
                if (this.state.type === 'nisab') {
                    setTimeout(() => {
                        this.fetchNisabInfo();
                    }, 500);
                } else {
                    this.state.step = 2;
                    setTimeout(() => {
                        this.askNextQuestion();
                    }, 500);
                }
            });
        });
        
        cancelBtns.forEach(btn => {
            if (!btn.dataset.zakatCancelAttached) {
                btn.addEventListener('click', () => this.cancel());
                btn.dataset.zakatCancelAttached = '1';
            }
        });
    }

    showNisabYearSelection() {
        this.state = {
            active: true,
            type: 'nisab',
            step: 0,
            data: {},
            yearType: null,
            year: null,
            availableYears: []
        };
        
        this.zakatTypes.nisab = {
            name: 'Maklumat Nisab',
            icon: '📊',
            steps: ['year_type', 'year'],
            prompts: {
                year_type: 'Sila pilih jenis tahun:',
                year: 'Sila pilih tahun:'
            }
        };
        
        setTimeout(() => {
            this.showYearTypeSelection();
        }, 300);
    }

    askNextQuestion() {
        const config = this.zakatTypes[this.state.type];
        const currentStepName = config.steps[this.state.step];
        const prompt = config.prompts[currentStepName];
        
        if (currentStepName !== 'year_type' && currentStepName !== 'year') {
            this.chatbot.appendMessage(prompt, 'bot');
        }
    }

    processInput(message) {
        // Check if reminder handler is active first
        if (this.reminderHandler && this.reminderHandler.isActive()) {
            return this.reminderHandler.processInput(message);
        }
        
        if (!this.state.active) return false;
        
        if (this.state.step < 2) {
            this.chatbot.appendMessage('Sila gunakan butang untuk memilih.', 'bot');
            return true;
        }
        
        const config = this.zakatTypes[this.state.type];
        const currentStepName = config.steps[this.state.step];
        
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
        
        if (this.state.step >= config.steps.length) {
            this.calculateZakat();
            return true;
        }
        
        setTimeout(() => {
            this.askNextQuestion();
        }, 500);
        
        return true;
    }

    validateInput(message, stepName) {
        const cleaned = message.replace(/[RM,\s]/gi, '').trim();
        const number = parseFloat(cleaned);
        
        if (isNaN(number) || number < 0) {
            return null;
        }
        
        return number;
    }

    async calculateZakat() {
        this.chatbot.setTyping(true);
        
        try {
            const payload = {
                type: this.state.type,
                amount: this.state.data.amount,
                year: this.state.year,
                year_type: this.state.yearType
            };
            
            if (this.state.type === 'income') {
                payload.expenses = this.state.data.expenses;
            }
            
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/calculate-zakat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data.success) {
                setTimeout(() => {
                    this.displayResult(data.reply, data.data);
                    
                    // Check if zakat exceeds nisab and offer reminder
                    if (data.data.reaches_nisab && data.data.zakat_amount > 0) {
                        setTimeout(() => {
                            this.offerReminder(data.data);
                        }, 1000);
                    }
                }, 800);
            } else {
                this.chatbot.appendMessage(
                    `❌ ${data.error || 'Ralat pengiraan. Sila cuba lagi.'}`,
                    'bot'
                );
            }
            
        } catch (error) {
            console.error('Zakat calculation error:', error);
            this.chatbot.appendMessage(
                '❌ Maaf, sistem ralat. Sila cuba lagi.',
                'bot'
            );
        } finally {
            this.chatbot.setTyping(false);
            this.resetState();
        }
    }

    displayResult(message, data) {
        const resultHTML = `
            <div class="zakat-result-card ${data.reaches_nisab ? 'success' : ''}">
                ${this.formatMessage(message)}
                ${this.createActionButtons(data)}
            </div>
        `;
        
        this.chatbot.appendMessage(resultHTML, 'bot', true);
        this.animateResult();
    }

    formatMessage(message) {
        const paragraphs = message.split('\n\n').map(para => {
            const formatted = para.replace(/\n/g, '<br>');
            const withBold = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            return `<p>${withBold}</p>`;
        }).join('');
        
        return paragraphs;
    }

    createActionButtons(data) {
        return `
            <div class="zakat-action-buttons">
                <button class="btn-recalculate" onclick="window.zakatHandler.showZakatMenu()">
                    🔄 Kira Semula
                </button>
            </div>
        `;
    }

    animateResult() {
        const cards = document.querySelectorAll('.zakat-result-card');
        const lastCard = cards[cards.length - 1];
        
        if (lastCard) {
            lastCard.style.opacity = '0';
            lastCard.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                lastCard.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                lastCard.style.opacity = '1';
                lastCard.style.transform = 'translateY(0)';
            }, 100);
        }
    }


// Update the offerReminder method in zakat-handler.js
// This ensures the zakat type is properly passed to the reminder handler

offerReminder(zakatData) {
    // Map the calculation type to proper zakat type name
    const zakatTypeMap = {
        'income': 'pendapatan',
        'savings': 'simpanan'
    };
    
    const zakatType = zakatTypeMap[this.state.type] || this.state.type;
    
    console.log('Offering reminder with:', {
        type: zakatType,
        amount: zakatData.zakat_amount
    });
    
    // Start reminder flow with proper zakat type
    if (this.reminderHandler) {
        this.reminderHandler.startReminderFlow(
            zakatType,
            zakatData.zakat_amount
        );
    }
}
    

    async fetchNisabInfo() {
        if (this.state.year && this.state.yearType) {
            this.chatbot.setTyping(true);
            
            try {
                const response = await fetch(
                    `${window.CONFIG.API_BASE_URL}/zakat/nisab-info?year=${this.state.year}&type=${this.state.yearType}`
                );
                const data = await response.json();
                
                if (data.success) {
                    setTimeout(() => {
                        this.chatbot.setTyping(false);
                        const formattedMessage = this.formatMessage(data.reply);
                        this.chatbot.appendMessage(formattedMessage, 'bot', true);
                        this.resetState();
                    }, 500);
                } else {
                    throw new Error(data.error || 'Gagal mendapatkan maklumat nisab');
                }
            } catch (error) {
                console.error('Nisab info error:', error);
                this.chatbot.setTyping(false);
                this.chatbot.appendMessage('❌ Ralat mendapatkan maklumat nisab. Sila cuba lagi.', 'bot');
                this.resetState();
            }
        } else {
            this.showNisabYearSelection();
        }
    }

    resetState() {
        this.state = {
            active: false,
            type: null,
            step: 0,
            data: {},
            yearType: null,
            year: null,
            availableYears: []
        };
    }

    cancel() {
        if (this.state.active) {
            this.chatbot.appendMessage(
                '❌ Pengiraan zakat dibatalkan. Taip "kira zakat" untuk cuba lagi.',
                'bot'
            );
            this.resetState();
        }
    }

    isBusy() {
        return this.state.active || (this.reminderHandler && this.reminderHandler.isActive());
    }
}

window.ZakatHandler = ZakatHandler;