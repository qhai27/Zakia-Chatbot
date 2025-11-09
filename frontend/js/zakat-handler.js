/**
 * Manages interactive zakat calculation flow with year selection
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
                    this.showNisabYearSelection();
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
            data: {},
            yearType: null,
            year: null,
            availableYears: []
        };
        
        // Show year type selection first
        setTimeout(() => {
            this.showYearTypeSelection();
        }, 500);
    }

    /**
     * Show year type selection (Hijrah/Masihi)
     */
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

    /**
     * Attach listeners to year type buttons
     */
    attachYearTypeListeners() {
        const buttons = document.querySelectorAll('.zakat-year-type-btn');
        const cancelBtns = document.querySelectorAll('.zakat-cancel-btn');
        const attachCancelOnce = (el) => {
            if (!el || el.dataset.zakatCancelAttached) return;
            el.addEventListener('click', () => this.cancel());
            el.dataset.zakatCancelAttached = '1';
        };
        
        buttons.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const yearType = e.target.getAttribute('data-year-type');
                
                // Disable all buttons
                buttons.forEach(b => b.disabled = true);
                cancelBtns.forEach(cb => cb.disabled = true);
                e.target.classList.add('selected');
                
                this.state.yearType = yearType;
                
                // Fetch available years
                await this.fetchAndShowYears(yearType);
            });
        });
        
        // attach to any cancel buttons in the current message(s)
        cancelBtns.forEach(attachCancelOnce);
    }
    
    /**
     * Fetch and show available years
     */
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
            
            // Use default years 
            const defaultYears = yearType === 'H' 
                ? ['1448','1447', '1446', '1445', '1444', '1443'] 
                : ['2025' , '2024', '2023', '2022', '2021', '2020'];
            
            this.chatbot.appendMessage(
                'ℹ️ Menggunakan tahun tersedia...',
                'bot'
            );
            
            setTimeout(() => {
                this.showYearSelection(defaultYears, yearType);
            }, 300);
        }
    }

    /**
     * Show year selection buttons
     */
    showYearSelection(years, yearType) {
        const config = this.zakatTypes[this.state.type];
        const yearLabel = yearType === 'H' ? 'Hijrah' : 'Masihi';
        
    
        const yearArray = Array.isArray(years) ? years : [];
        const displayYears = yearArray.slice(0, 5);
        
        if (displayYears.length === 0) {
            // If no years available, use defaults
            displayYears.push(...(yearType === 'H' 
                ? ['1448', '1447', '1446', '1445'] 
                : ['2025', '2024', '2023', '2022']));
        }
        
        // Create year buttons
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

    /**
     * Attach listeners to year selection buttons
     */
    attachYearListeners() {
        const buttons = document.querySelectorAll('.zakat-year-btn');
        const cancelBtns = document.querySelectorAll('.zakat-cancel-btn');
        const attachCancelOnce = (el) => {
            if (!el || el.dataset.zakatCancelAttached) return;
            el.addEventListener('click', () => this.cancel());
            el.dataset.zakatCancelAttached = '1';
        };
        
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const year = e.target.getAttribute('data-year');
                
                // Disable all buttons
                buttons.forEach(b => b.disabled = true);
                cancelBtns.forEach(cb => cb.disabled = true);
                e.target.classList.add('selected');
                
                this.state.year = year;
                
                // Check if this is for nisab info or calculation
                if (this.state.type === 'nisab') {
                    // Fetch nisab info directly
                    setTimeout(() => {
                        this.fetchNisabInfo();
                    }, 500);
                } else {
                    // Continue with calculation
                    this.state.step = 2; // Move to amount input
                    setTimeout(() => {
                        this.askNextQuestion();
                    }, 500);
                }
            });
        });
        
        // attach to any cancel buttons in the current message(s)
        cancelBtns.forEach(attachCancelOnce);
    }

    /**
     * Show nisab year selection for info query
     */
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
        
        // Override the prompts for nisab query
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

    /**
     * Ask next question in the flow
     */
    askNextQuestion() {
        const config = this.zakatTypes[this.state.type];
        const currentStepName = config.steps[this.state.step];
        const prompt = config.prompts[currentStepName];
        
        if (currentStepName !== 'year_type' && currentStepName !== 'year') {
            this.chatbot.appendMessage(prompt, 'bot');
        }
    }

    /**
     * Process user input during calculation
     */
    processInput(message) {
        if (!this.state.active) return false;
        
        // If waiting for year selection, ignore text input
        if (this.state.step < 2) {
            this.chatbot.appendMessage(
                'Sila gunakan butang untuk memilih.',
                'bot'
            );
            return true;
        }
        
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
        setTimeout(() => {
            this.askNextQuestion();
        }, 500);
        
        return true;
    }

    /**
     * Validate user input
     */
    validateInput(message, stepName) {
        // Remove RM, comma, and whitespace
        const cleaned = message.replace(/[RM,\s]/gi, '').trim();
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
                amount: this.state.data.amount,
                year: this.state.year,
                year_type: this.state.yearType
            };
            
            // Add type-specific data
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

    /**
     * Display calculation result
     */
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

    /**
     * Format message with proper styling
     */
    formatMessage(message) {
        // Split by double newline for paragraphs
        const paragraphs = message.split('\n\n').map(para => {
            // Replace single newlines with <br>
            const formatted = para.replace(/\n/g, '<br>');
            // Make **text** bold
            const withBold = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            return `<p>${withBold}</p>`;
        }).join('');
        
        return paragraphs;
    }

    /**
     * Create action buttons
     */
    createActionButtons(data) {
        return `
            <div class="zakat-action-buttons">
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

    /**
     * Fetch nisab information
     */
    async fetchNisabInfo() {
        // If year already selected, fetch info
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
            // Need to select year first, start the flow
            this.showNisabYearSelection();
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
            data: {},
            yearType: null,
            year: null,
            availableYears: []
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
    
    /**
     * Get current calculation summary
     */
    getCalculationSummary() {
        if (!this.state.active) return null;
        
        const config = this.zakatTypes[this.state.type];
        return {
            type: config.name,
            yearType: this.state.yearType ? (this.state.yearType === 'H' ? 'Hijrah' : 'Masihi') : null,
            year: this.state.year,
            step: this.state.step,
            totalSteps: config.steps.length,
            data: this.state.data
        };
    }
    
    /**
     * Check if handler is busy
     */
    isBusy() {
        return this.state.active;
    }
}

// Export for use in main chatbot
window.ZakatHandler = ZakatHandler;