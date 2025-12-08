/**
 * Updated ZakatHandler with Kaedah A (Tanpa Tolakan) and Kaedah B (Dengan Tolakan)
 * Manages zakat calculation with two income calculation methods
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
            availableYears: [],
            incomeMethod: null // 'kaedah_a' or 'kaedah_b'
        };

        // Initialize reminder handler
        this.reminderHandler = new window.ReminderHandler(chatbot);

        this.zakatTypes = {
            income_kaedah_a: {
                name: 'Zakat Pendapatan (Kaedah A)',
                icon: '💼',
                steps: ['year_type', 'year', 'amount'],
                prompts: {
                    year_type: 'Sila pilih jenis tahun:',
                    year: 'Sila pilih tahun:',
                    amount: '💼 Sila masukkan jumlah pendapatan kasar tahunan anda (RM):'
                }
            },
            income_kaedah_b: {
                name: 'Zakat Pendapatan (Kaedah B)',
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

        if (msg.includes('emas') || msg.includes('bulanan') || 
            msg.includes('perak') || msg.includes('tahunan') ||
            msg.includes('dikira') || msg.includes('zakat perniagaan') ||
            msg.includes('zakat ternakan') || msg.includes('zakat pertanian')||
            msg.includes('pelaburan')) {
            return null;
        }

        if (msg.includes('kira zakat pendapatan') ||
            msg.includes('zakat pendapatan') ||
            msg.includes('zakat gaji') ||
            msg.includes('zakat income')) {
            return 'income_menu';
        }

        if (msg.includes('kira zakat simpanan') ||
            msg.includes('zakat simpanan') ||
            msg.includes('zakat wang') ||
            msg.includes('zakat savings')) {
            return 'savings';
        }

        if ((msg.includes('kira zakat') || msg.includes('zakat kalkulator') || msg.includes('kalkulator zakat')) &&
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
                    <button class="zakat-type-btn" data-type="income_menu">
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

    showIncomeMethodMenu() {
        const menuHTML = `
            <div class="zakat-menu">
                <p style="margin-bottom: 16px; font-weight: 600;">💼 Pilih kaedah pengiraan zakat pendapatan:</p>
                <div class="zakat-method-info" style="background: #f0f9ff; padding: 12px; border-radius: 8px; margin-bottom: 12px; font-size: 0.9em;">
                    <p style="margin: 0 0 8px 0;"><strong>Kaedah A:</strong> Pengiraan tanpa tolakan perbelanjaan (pendapatan kasar)</p>
                    <p style="margin: 0;"><strong>Kaedah B:</strong> Pengiraan dengan tolakan perbelanjaan asas</p>
                </div>
                <div class="zakat-buttons">
                    <button class="zakat-method-btn" data-method="kaedah_a">
                        📋 Kaedah A (Tanpa Tolakan)
                    </button>
                    <button class="zakat-method-btn" data-method="kaedah_b">
                        📊 Kaedah B (Dengan Tolakan)
                    </button>
                    <button class="zakat-cancel-btn">
                        ❌ Batal
                    </button>
                </div>
            </div>
        `;

        this.chatbot.appendMessage(menuHTML, 'bot', true);
        this.attachMethodMenuListeners();
    }

    attachMethodMenuListeners() {
        const buttons = document.querySelectorAll('.zakat-method-btn');
        const cancelBtns = document.querySelectorAll('.zakat-cancel-btn');

        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const method = e.target.getAttribute('data-method');
                buttons.forEach(b => b.disabled = true);
                cancelBtns.forEach(cb => cb.disabled = true);
                e.target.classList.add('selected');

                const type = method === 'kaedah_a' ? 'income_kaedah_a' : 'income_kaedah_b';
                this.startZakatCalculation(type);
            });
        });

        cancelBtns.forEach(btn => {
            if (!btn.dataset.zakatCancelAttached) {
                btn.addEventListener('click', () => this.cancel());
                btn.dataset.zakatCancelAttached = '1';
            }
        });
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
                } else if (type === 'income_menu') {
                    setTimeout(() => {
                        this.showIncomeMethodMenu();
                    }, 500);
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
            availableYears: [],
            incomeMethod: type.includes('kaedah_a') ? 'kaedah_a' : (type.includes('kaedah_b') ? 'kaedah_b' : null)
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
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/api/zakat/years?type=${yearType}`);
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
                ? ['1448', '1447', '1446', '1445']
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
        let shouldResetState = true;

        try {
            const payload = {
                year: this.state.year,
                year_type: this.state.yearType
            };

            // Determine calculation type and payload structure
            if (this.state.type === 'income_kaedah_a') {
                payload.type = 'income_kaedah_a';
                payload.amount = this.state.data.amount;
            } else if (this.state.type === 'income_kaedah_b') {
                payload.type = 'income_kaedah_b';
                payload.amount = this.state.data.amount;
                payload.expenses = this.state.data.expenses;
            } else if (this.state.type === 'savings') {
                payload.type = 'savings';
                payload.amount = this.state.data.amount;
            }

            const response = await fetch(`${window.CONFIG.API_BASE_URL}/api/calculate-zakat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                const zakatType = this.state.type;
                const year = this.state.year;
                const yearType = this.state.yearType;

                if (data.data.reaches_nisab && data.data.zakat_amount > 0) {
                    shouldResetState = false;
                }

                setTimeout(() => {
                    this.displayResult(data.reply, data.data);

                    if (data.data.reaches_nisab && data.data.zakat_amount > 0) {
                        setTimeout(() => {
                            this.offerReminder(data.data, zakatType, year, yearType);
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
            if (shouldResetState) {
                this.resetState();
            }
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
        const paymentButton = data.reaches_nisab && data.zakat_amount > 0 ? `
            <button class="btn-pay-zakat" onclick="window.zakatHandler.openPaymentPage()">
                💳 Bayar Zakat
            </button>
        ` : '';
        
        return `
            <div class="zakat-action-buttons vertical-stack">
                ${paymentButton}
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

    offerReminder(zakatData, zakatTypeFromState = null, yearFromState = null, yearTypeFromState = null) {
        const zakatTypeMap = {
            'income_kaedah_a': 'pendapatan',
            'income_kaedah_b': 'pendapatan',
            'savings': 'simpanan'
        };

        const stateType = zakatTypeFromState !== null ? zakatTypeFromState : this.state.type;
        let zakatType = zakatTypeMap[stateType] || stateType;

        if (!zakatType || (zakatType !== 'pendapatan' && zakatType !== 'simpanan')) {
            console.warn('Invalid zakat type, defaulting to pendapatan:', zakatType);
            zakatType = 'pendapatan';
        }

        const year = yearFromState !== null ? yearFromState : (this.state.year || '');
        const yearType = yearTypeFromState !== null ? yearTypeFromState : (this.state.yearType || 'M');

        if (this.reminderHandler) {
            this.reminderHandler.startReminderFlow(
                zakatType,
                zakatData.zakat_amount,
                year,
                yearType
            );

            setTimeout(() => {
                this.resetState();
            }, 100);
        } else {
            this.resetState();
        }
    }

    async fetchNisabInfo() {
        if (this.state.year && this.state.yearType) {
            this.chatbot.setTyping(true);

            try {
                const response = await fetch(
                    `${window.CONFIG.API_BASE_URL}/api/zakat/nisab-info?year=${this.state.year}&type=${this.state.yearType}`
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

    openPaymentPage() {
        const paymentUrl = 'https://jom.zakatkedah.com.my';
        window.open(paymentUrl, '_blank', 'noopener,noreferrer');
        
        this.chatbot.appendMessage(
            '✅ Halaman pembayaran JomZakat telah dibuka. Sila lengkapkan pembayaran zakat anda di tab baru. 🙏',
            'bot'
        );
    }

    resetState() {
        this.state = {
            active: false,
            type: null,
            step: 0,
            data: {},
            yearType: null,
            year: null,
            availableYears: [],
            incomeMethod: null
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