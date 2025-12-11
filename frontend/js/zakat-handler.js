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
            },
            padi: {
                name: 'Zakat Padi',
                icon: '🌾',
                steps: ['year_type', 'year', 'jumlah_hasil_rm'],
                prompts: {
                    year_type: 'Sila pilih jenis tahun:',
                    year: 'Sila pilih tahun:',
                    jumlah_hasil_rm: '🌾 Sila masukkan jumlah hasil padi anda dalam RM:'
                }
            },
            saham: {
                name: 'Zakat Saham',
                icon: '📈',
                steps: ['year_type', 'year', 'nilai_portfolio', 'hutang_saham'],
                prompts: {
                    year_type: 'Sila pilih jenis tahun:',
                    year: 'Sila pilih tahun:',
                    nilai_portfolio: '📈 Sila masukkan nilai portfolio saham anda (RM):',
                    hutang_saham: '💳 Sila masukkan hutang saham (RM) [kosongkan jika tiada]:'
                }
            },
            perak: {
                name: 'Zakat Perak',
                icon: '🥈',
                steps: ['year_type', 'year', 'berat_perak_g', 'harga_per_gram'],
                prompts: {
                    year_type: 'Sila pilih jenis tahun:',
                    year: 'Sila pilih tahun:',
                    berat_perak_g: '🥈 Sila masukkan berat perak anda (gram):',
                    harga_per_gram: '💰 Sila masukkan harga perak per gram (RM):'
                }
            },
            kwsp: {
                name: 'Zakat KWSP',
                icon: '🏦',
                steps: ['year_type', 'year', 'jumlah_akaun_1', 'jumlah_akaun_2', 'jumlah_pengeluaran'],
                prompts: {
                    year_type: 'Sila pilih jenis tahun:',
                    year: 'Sila pilih tahun:',
                    jumlah_akaun_1: '💼 Sila masukkan jumlah Akaun 1 (RM):',
                    jumlah_akaun_2: '💼 Sila masukkan jumlah Akaun 2 (RM):',
                    jumlah_pengeluaran: '💳 Sila masukkan jumlah pengeluaran (RM) [kosongkan jika tiada]:'
                }
            }
        };
    }

    detectZakatIntent(message) {
        const msg = message.toLowerCase();

        if (msg.includes('emas') || msg.includes('bulanan') ||
            msg.includes('perak') || msg.includes('tahunan') ||
            msg.includes('dikira') || msg.includes('zakat perniagaan') ||
            msg.includes('zakat ternakan') || msg.includes('zakat pertanian') ||
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

        if (msg.includes('kira zakat padi') ||
            msg.includes('zakat padi') ||
            msg.includes('zakat beras')) {
            return 'padi';
        }

        if (msg.includes('kira zakat saham') ||
            msg.includes('zakat saham') ||
            msg.includes('zakat portfolio')) {
            return 'saham';
        }

        if (msg.includes('kira zakat perak') ||
            msg.includes('zakat perak') ||
            msg.includes('zakat silver')) {
            return 'perak';
        }

        if (msg.includes('kira zakat kwsp') ||
            msg.includes('zakat kwsp') ||
            msg.includes('zakat epf')) {
            return 'kwsp';
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
                <p style="margin-bottom: 16px; font-weight: 600;">Pilih jenis zakat yang ingin dikira:</p>
                <div class="zakat-buttons">
                    <button class="zakat-type-btn" data-type="income_menu">
                        💼 Zakat Pendapatan
                    </button>
                    <button class="zakat-type-btn" data-type="savings">
                        💰 Zakat Simpanan
                    </button>
                    <button class="zakat-type-btn" data-type="kwsp">
                        🏦Zakat KWSP
                    </button>
                    <button class="zakat-type-btn" data-type="saham">
                        📈 Zakat Saham
                    </button>
                    <button class="zakat-type-btn" data-type="perak">
                        🥈 Zakat Perak
                    </button>
                    <button class="zakat-type-btn" data-type="padi">
                        🌾 Zakat Padi
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
                
                            
            <div class="zakat-method-info" style="background:#f3f7f4; padding:8px; border-radius:6px; font-size:1em; color:#1a1a1a; line-height:1.2; display:inline-block;">

                <!-- Kaedah A -->
                <strong>Kaedah A (Disyorkan) ⭐</strong><br>
                📌 Pengiraan tanpa tolakan (pendapatan kasar)<br>
                <span style="font-size:0.95em;">
                    • ⚡ Mudah & cepat  
                    • 🛡️ Kurang risiko silap  
                    • 📘 Selaras majoriti fatwa
                </span><br>
                <span style="font-size:0.95em;"><strong>Formula:</strong> (Pendapatan Kasar Tahunan × 2.5%)</span>

                <div style="border-top:1px solid #c5d3c7; margin:4px 0;"></div>

                <!-- Kaedah B -->
                <strong>Kaedah B 🧮</strong><br>
                📌 Selepas tolak perbelanjaan asas<br>
                <span style="font-size:0.95em;">
                    • 👍 Sesuai jika perbelanjaan asas tinggi  
                    • 📌 Perlu teliti antara keperluan & kehendak
                </span><br>
                <span style="font-size:0.95em;"><strong>Formula:</strong> (Pendapatan – Perbelanjaan Asas) × 2.5%</span>

                <!-- Cadangan -->
                <div style="margin-top:4px; padding:6px; background:#e1f0e5; border-radius:4px; border-left:4px solid #2f6b3a; font-size:0.95em; color:#10391e; font-weight:600; line-height:1.2;">
                    💡 <strong>Cadangan:</strong> Pilih <strong>Kaedah A</strong> untuk kiraan paling stabil, tepat & selamat.
                </div>

            </div>


                <div class="zakat-buttons">
                    <button class="zakat-type-btn" data-method="kaedah_a">
                        📋 Kaedah A (Tanpa Tolakan)
                    </button>
                    <button class="zakat-type-btn" data-method="kaedah_b">
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
        const buttons = document.querySelectorAll('.zakat-type-btn[data-method]');
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
        // Allow empty for optional fields
        const cleaned = message.replace(/[RM,\s]/gi, '').trim();

        // Optional fields: hutang_saham, jumlah_pengeluaran
        if ((stepName === 'hutang_saham' || stepName === 'jumlah_pengeluaran') && cleaned === '') {
            return 0; // Default to 0 for optional fields
        }

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
            let payload = {};

            // Build payload based on zakat type - backend expects specific parameter names
            if (this.state.type === 'income_kaedah_a') {
                payload = {
                    type: 'income_kaedah_a',
                    gross_income: this.state.data.amount,
                    year: this.state.year,
                    year_type: this.state.yearType
                };
            } else if (this.state.type === 'income_kaedah_b') {
                payload = {
                    type: 'income_kaedah_b',
                    annual_income: this.state.data.amount,
                    annual_expenses: this.state.data.expenses,
                    year: this.state.year,
                    year_type: this.state.yearType
                };
            } else if (this.state.type === 'savings') {
                payload = {
                    type: 'savings',
                    savings_amount: this.state.data.amount,
                    year: this.state.year,
                    year_type: this.state.yearType
                };
            } else if (this.state.type === 'padi') {
                // padi now accepts jumlah_rm (total value in RM)
                payload = {
                    jumlah_rm: Number(this.state.data.jumlah_hasil_rm) || 0,
                    year: this.state.year,
                    year_type: this.state.yearType
                };
            } else if (this.state.type === 'saham') {
                payload = {
                    nilai_portfolio: this.state.data.nilai_portfolio,
                    hutang_saham: this.state.data.hutang_saham || 0,
                    year: this.state.year,
                    year_type: this.state.yearType
                };
            } else if (this.state.type === 'perak') {
                payload = {
                    berat_perak_g: this.state.data.berat_perak_g,
                    harga_per_gram: this.state.data.harga_per_gram,
                    year: this.state.year,
                    year_type: this.state.yearType
                };
            } else if (this.state.type === 'kwsp') {
                payload = {
                    jumlah_akaun_1: this.state.data.jumlah_akaun_1,
                    jumlah_akaun_2: this.state.data.jumlah_akaun_2,
                    jumlah_pengeluaran: this.state.data.jumlah_pengeluaran || 0,
                    year: this.state.year,
                    year_type: this.state.yearType
                };
            } else {
                throw new Error('Jenis zakat tidak dikenali');
            }

            console.log('Sending payload:', payload); // Debug log

            // Determine API endpoint based on zakat type
            let apiEndpoint = '/api/calculate-zakat';
            if (['padi', 'saham', 'perak', 'kwsp'].includes(this.state.type)) {
                apiEndpoint = `/zakat-calculator/${this.state.type}`;
            }

            const response = await fetch(`${window.CONFIG.API_BASE_URL}${apiEndpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            console.log('Received response:', data); // Debug log

            if (data.success) {
                // Use type from response data if available, otherwise use state type
                const zakatType = data.data.type || this.state.type;
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

    /**
 * Attach listeners to extended zakat type buttons
 */
    attachExtendedTypeListeners() {
        const buttons = document.querySelectorAll('.zakat-type-btn');
        const cancelBtn = document.querySelector('.zakat-cancel-btn');

        buttons.forEach(btn => {
            if (btn.dataset._zakatAttached) return;
            btn.dataset._zakatAttached = '1';

            btn.addEventListener('click', (e) => {
                const type = e.currentTarget.getAttribute('data-type');

                // Disable all buttons
                buttons.forEach(b => b.disabled = true);
                e.currentTarget.classList.add('selected');

                this.state.zakatType = type;

                setTimeout(() => {
                    this.askYearSelection(type);
                }, 500);
            });
        });

        if (cancelBtn && !cancelBtn.dataset._zakatAttached) {
            cancelBtn.dataset._zakatAttached = '1';
            cancelBtn.addEventListener('click', () => {
                this.cancel();
            });
        }
    }

    /**
     * Show input form for Padi
     */
    showPadiForm(year, yearType) {
        this.state.year = year;
        this.state.yearType = yearType;
        this.state.waitingFor = 'padi_calculation';

        const html = `
        <div class="zakat-input-form">
            <p style="font-weight: 600; color: #157347; margin-bottom: 16px;">
                🌾 Kalkulator Zakat Padi
            </p>
            
            <div class="zakat-method-info">
                <p><strong>Formula:</strong> Zakat = Hasil Padi (kg) × Harga Beras (RM/kg) × 10%</p>
                <p><strong>Nisab:</strong> 1,300 kg padi</p>
            </div>
            
            <div class="form-group">
                <label>Hasil Padi (kg) <span style="color: red;">*</span></label>
                <input type="number" 
                       id="hasil_padi_kg" 
                       class="zakat-input" 
                       placeholder="Contoh: 2000"
                       min="0"
                       step="0.01">
            </div>
            
            <div class="form-group">
                <label>Harga Beras (RM/kg) <span style="color: red;">*</span></label>
                <input type="number" 
                       id="harga_beras_kg" 
                       class="zakat-input" 
                       placeholder="Contoh: 3.50"
                       min="0"
                       step="0.01">
            </div>
            
            <div class="zakat-buttons">
                <button class="zakat-type-btn" data-action="calculate-padi">
                    🧮 Kira Zakat
                </button>
                <button class="zakat-cancel-btn" data-action="cancel">
                    ❌ Batal
                </button>
            </div>
        </div>
    `;

        this.chatbot.appendMessage(html, 'bot', true);
        this.attachPadiFormListeners();
    }

    /**
     * Attach listeners to Padi form
     */
    attachPadiFormListeners() {
        const calculateBtn = document.querySelector('[data-action="calculate-padi"]');
        const cancelBtn = document.querySelector('[data-action="cancel"]');

        if (calculateBtn && !calculateBtn.dataset._attached) {
            calculateBtn.dataset._attached = '1';
            calculateBtn.addEventListener('click', async () => {
                await this.calculatePadi();
            });
        }

        if (cancelBtn && !cancelBtn.dataset._attached) {
            cancelBtn.dataset._attached = '1';
            cancelBtn.addEventListener('click', () => {
                this.cancel();
            });
        }
    }

    /**
     * Calculate Padi Zakat
     */
    async calculatePadi() {
        const hasilInput = document.getElementById('hasil_padi_kg');
        const hargaInput = document.getElementById('harga_beras_kg');

        if (!hasilInput || !hargaInput) return;

        const hasil = parseFloat(hasilInput.value);
        const harga = parseFloat(hargaInput.value);

        // Validation
        if (!hasil || hasil <= 0) {
            this.chatbot.appendMessage('⚠️ Sila masukkan hasil padi yang sah.', 'bot');
            return;
        }

        if (!harga || harga <= 0) {
            this.chatbot.appendMessage('⚠️ Sila masukkan harga beras yang sah.', 'bot');
            return;
        }

        // Show calculating message
        this.chatbot.setTyping(true);
        this.chatbot.appendMessage('Mengira zakat padi...', 'bot');

        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/api/calculate-zakat-padi`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    hasil_padi_kg: hasil,
                    harga_beras_kg: harga,
                    year: this.state.year,
                    year_type: this.state.yearType
                })
            });

            const data = await response.json();

            setTimeout(() => {
                this.chatbot.setTyping(false);

                if (data.success && data.data) {
                    this.showResultCard(data.data, data.reply);
                } else {
                    this.chatbot.appendMessage(
                        `❌ ${data.error || 'Ralat pengiraan. Sila cuba lagi.'}`,
                        'bot'
                    );
                }
            }, 800);

        } catch (error) {
            console.error('Error calculating padi zakat:', error);
            this.chatbot.setTyping(false);
            this.chatbot.appendMessage('❌ Ralat sistem. Sila cuba lagi.', 'bot');
        }
    }

    /**
     * Show input form for Saham
     */
    showSahamForm(year, yearType) {
        this.state.year = year;
        this.state.yearType = yearType;
        this.state.waitingFor = 'saham_calculation';

        const html = `
        <div class="zakat-input-form">
            <p style="font-weight: 600; color: #157347; margin-bottom: 16px;">
                📈 Kalkulator Zakat Saham
            </p>
            
            <div class="zakat-method-info">
                <p><strong>Formula:</strong> Zakat = (Nilai Portfolio - Hutang) × 2.5%</p>
                <p><strong>Nisab:</strong> 85 gram emas</p>
            </div>
            
            <div class="form-group">
                <label>Nilai Portfolio (RM) <span style="color: red;">*</span></label>
                <input type="number" 
                       id="nilai_portfolio" 
                       class="zakat-input" 
                       placeholder="Contoh: 50000"
                       min="0"
                       step="0.01">
            </div>
            
            <div class="form-group">
                <label>Hutang Saham (RM)</label>
                <input type="number" 
                       id="hutang_saham" 
                       class="zakat-input" 
                       placeholder="Contoh: 0"
                       min="0"
                       step="0.01"
                       value="0">
            </div>
            
            <div class="zakat-buttons">
                <button class="zakat-type-btn" data-action="calculate-saham">
                    🧮 Kira Zakat
                </button>
                <button class="zakat-cancel-btn" data-action="cancel">
                    ❌ Batal
                </button>
            </div>
        </div>
    `;

        this.chatbot.appendMessage(html, 'bot', true);
        this.attachSahamFormListeners();
    }

    /**
     * Attach listeners to Saham form
     */
    attachSahamFormListeners() {
        const calculateBtn = document.querySelector('[data-action="calculate-saham"]');
        const cancelBtn = document.querySelector('[data-action="cancel"]');

        if (calculateBtn && !calculateBtn.dataset._attached) {
            calculateBtn.dataset._attached = '1';
            calculateBtn.addEventListener('click', async () => {
                await this.calculateSaham();
            });
        }

        if (cancelBtn && !cancelBtn.dataset._attached) {
            cancelBtn.dataset._attached = '1';
            cancelBtn.addEventListener('click', () => {
                this.cancel();
            });
        }
    }

    /**
     * Calculate Saham Zakat
     */
    async calculateSaham() {
        const portfolioInput = document.getElementById('nilai_portfolio');
        const hutangInput = document.getElementById('hutang_saham');

        if (!portfolioInput) return;

        const portfolio = parseFloat(portfolioInput.value);
        const hutang = hutangInput ? parseFloat(hutangInput.value) || 0 : 0;

        // Validation
        if (!portfolio || portfolio <= 0) {
            this.chatbot.appendMessage('⚠️ Sila masukkan nilai portfolio yang sah.', 'bot');
            return;
        }

        // Show calculating message
        this.chatbot.setTyping(true);
        this.chatbot.appendMessage('Mengira zakat saham...', 'bot');

        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/api/calculate-zakat-saham`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nilai_portfolio: portfolio,
                    hutang_saham: hutang,
                    year: this.state.year,
                    year_type: this.state.yearType
                })
            });

            const data = await response.json();

            setTimeout(() => {
                this.chatbot.setTyping(false);

                if (data.success && data.data) {
                    this.showResultCard(data.data, data.reply);
                } else {
                    this.chatbot.appendMessage(
                        `❌ ${data.error || 'Ralat pengiraan. Sila cuba lagi.'}`,
                        'bot'
                    );
                }
            }, 800);

        } catch (error) {
            console.error('Error calculating saham zakat:', error);
            this.chatbot.setTyping(false);
            this.chatbot.appendMessage('❌ Ralat sistem. Sila cuba lagi.', 'bot');
        }
    }

    /**
     * Show input form for Perak
     */
    showPerakForm(year, yearType) {
        this.state.year = year;
        this.state.yearType = yearType;
        this.state.waitingFor = 'perak_calculation';

        const html = `
        <div class="zakat-input-form">
            <p style="font-weight: 600; color: #157347; margin-bottom: 16px;">
                🥈 Kalkulator Zakat Perak
            </p>
            
            <div class="zakat-method-info">
                <p><strong>Formula:</strong> Zakat = (Berat × Harga) × 2.5%</p>
                <p><strong>Nisab:</strong> 595 gram perak</p>
            </div>
            
            <div class="form-group">
                <label>Berat Perak (gram) <span style="color: red;">*</span></label>
                <input type="number" 
                       id="berat_perak_g" 
                       class="zakat-input" 
                       placeholder="Contoh: 600"
                       min="0"
                       step="0.01">
            </div>
            
            <div class="form-group">
                <label>Harga Per Gram (RM) <span style="color: red;">*</span></label>
                <input type="number" 
                       id="harga_per_gram" 
                       class="zakat-input" 
                       placeholder="Contoh: 3.50"
                       min="0"
                       step="0.01">
            </div>
            
            <div class="zakat-buttons">
                <button class="zakat-type-btn" data-action="calculate-perak">
                    🧮 Kira Zakat
                </button>
                <button class="zakat-cancel-btn" data-action="cancel">
                    ❌ Batal
                </button>
            </div>
        </div>
    `;

        this.chatbot.appendMessage(html, 'bot', true);
        this.attachPerakFormListeners();
    }

    /**
     * Attach listeners to Perak form
     */
    attachPerakFormListeners() {
        const calculateBtn = document.querySelector('[data-action="calculate-perak"]');
        const cancelBtn = document.querySelector('[data-action="cancel"]');

        if (calculateBtn && !calculateBtn.dataset._attached) {
            calculateBtn.dataset._attached = '1';
            calculateBtn.addEventListener('click', async () => {
                await this.calculatePerak();
            });
        }

        if (cancelBtn && !cancelBtn.dataset._attached) {
            cancelBtn.dataset._attached = '1';
            cancelBtn.addEventListener('click', () => {
                this.cancel();
            });
        }
    }

    /**
     * Calculate Perak Zakat
     */
    async calculatePerak() {
        const beratInput = document.getElementById('berat_perak_g');
        const hargaInput = document.getElementById('harga_per_gram');

        if (!beratInput || !hargaInput) return;

        const berat = parseFloat(beratInput.value);
        const harga = parseFloat(hargaInput.value);

        // Validation
        if (!berat || berat <= 0) {
            this.chatbot.appendMessage('⚠️ Sila masukkan berat perak yang sah.', 'bot');
            return;
        }

        if (!harga || harga <= 0) {
            this.chatbot.appendMessage('⚠️ Sila masukkan harga per gram yang sah.', 'bot');
            return;
        }

        // Show calculating message
        this.chatbot.setTyping(true);
        this.chatbot.appendMessage('Mengira zakat perak...', 'bot');

        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/api/calculate-zakat-perak`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    berat_perak_g: berat,
                    harga_per_gram: harga,
                    year: this.state.year,
                    year_type: this.state.yearType
                })
            });

            const data = await response.json();

            setTimeout(() => {
                this.chatbot.setTyping(false);

                if (data.success && data.data) {
                    this.showResultCard(data.data, data.reply);
                } else {
                    this.chatbot.appendMessage(
                        `❌ ${data.error || 'Ralat pengiraan. Sila cuba lagi.'}`,
                        'bot'
                    );
                }
            }, 800);

        } catch (error) {
            console.error('Error calculating perak zakat:', error);
            this.chatbot.setTyping(false);
            this.chatbot.appendMessage('❌ Ralat sistem. Sila cuba lagi.', 'bot');
        }
    }

    /**
     * Show input form for KWSP
     */
    showKWSPForm(year, yearType) {
        this.state.year = year;
        this.state.yearType = yearType;
        this.state.waitingFor = 'kwsp_calculation';

        const html = `
        <div class="zakat-input-form">
            <p style="font-weight: 600; color: #157347; margin-bottom: 16px;">
                💼 Kalkulator Zakat KWSP
            </p>
            
            <div class="zakat-method-info">
                <p><strong>Formula:</strong></p>
                <p>• Jika ada pengeluaran: Zakat = Pengeluaran × 2.5%</p>
                <p>• Jika tiada pengeluaran: Zakat = (Akaun 1 + Akaun 2) × 2.5%</p>
                <p><strong>Nisab:</strong> 85 gram emas</p>
            </div>
            
            <div class="form-group">
                <label>Jumlah Akaun 1 (RM) <span style="color: red;">*</span></label>
                <input type="number" 
                       id="jumlah_akaun_1" 
                       class="zakat-input" 
                       placeholder="Contoh: 50000"
                       min="0"
                       step="0.01">
            </div>
            
            <div class="form-group">
                <label>Jumlah Akaun 2 (RM) <span style="color: red;">*</span></label>
                <input type="number" 
                       id="jumlah_akaun_2" 
                       class="zakat-input" 
                       placeholder="Contoh: 30000"
                       min="0"
                       step="0.01">
            </div>
            
            <div class="form-group">
                <label>Jumlah Pengeluaran (RM)</label>
                <input type="number" 
                       id="jumlah_pengeluaran" 
                       class="zakat-input" 
                       placeholder="Contoh: 0 (jika tiada)"
                       min="0"
                       step="0.01"
                       value="0">
                <small style="color: #666; font-size: 12px;">*Kosongkan jika tiada pengeluaran</small>
            </div>
            
            <div class="zakat-buttons">
                <button class="zakat-type-btn" data-action="calculate-kwsp">
                    🧮 Kira Zakat
                </button>
                <button class="zakat-cancel-btn" data-action="cancel">
                    ❌ Batal
                </button>
            </div>
        </div>
    `;

        this.chatbot.appendMessage(html, 'bot', true);
        this.attachKWSPFormListeners();
    }

    /**
     * Attach listeners to KWSP form
     */
    attachKWSPFormListeners() {
        const calculateBtn = document.querySelector('[data-action="calculate-kwsp"]');
        const cancelBtn = document.querySelector('[data-action="cancel"]');

        if (calculateBtn && !calculateBtn.dataset._attached) {
            calculateBtn.dataset._attached = '1';
            calculateBtn.addEventListener('click', async () => {
                await this.calculateKWSP();
            });
        }

        if (cancelBtn && !cancelBtn.dataset._attached) {
            cancelBtn.dataset._attached = '1';
            cancelBtn.addEventListener('click', () => {
                this.cancel();
            });
        }
    }

    /**
     * Calculate KWSP Zakat
     */
    async calculateKWSP() {
        const akaun1Input = document.getElementById('jumlah_akaun_1');
        const akaun2Input = document.getElementById('jumlah_akaun_2');
        const pengeluaranInput = document.getElementById('jumlah_pengeluaran');

        if (!akaun1Input || !akaun2Input) return;

        const akaun1 = parseFloat(akaun1Input.value);
        const akaun2 = parseFloat(akaun2Input.value);
        const pengeluaran = pengeluaranInput ? parseFloat(pengeluaranInput.value) || 0 : 0;

        // Validation
        if (!akaun1 || akaun1 < 0) {
            this.chatbot.appendMessage('⚠️ Sila masukkan jumlah Akaun 1 yang sah.', 'bot');
            return;
        }

        if (!akaun2 || akaun2 < 0) {
            this.chatbot.appendMessage('⚠️ Sila masukkan jumlah Akaun 2 yang sah.', 'bot');
            return;
        }

        // Show calculating message
        this.chatbot.setTyping(true);
        this.chatbot.appendMessage('Mengira zakat KWSP...', 'bot');

        try {
            const response = await fetch(`${window.CONFIG.API_BASE_URL}/api/calculate-zakat-kwsp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jumlah_akaun_1: akaun1,
                    jumlah_akaun_2: akaun2,
                    jumlah_pengeluaran: pengeluaran,
                    year: this.state.year,
                    year_type: this.state.yearType
                })
            });

            const data = await response.json();

            setTimeout(() => {
                this.chatbot.setTyping(false);

                if (data.success && data.data) {
                    this.showResultCard(data.data, data.reply);
                } else {
                    this.chatbot.appendMessage(
                        `❌ ${data.error || 'Ralat pengiraan. Sila cuba lagi.'}`,
                        'bot'
                    );
                }
            }, 800);

        } catch (error) {
            console.error('Error calculating KWSP zakat:', error);
            this.chatbot.setTyping(false);
            this.chatbot.appendMessage('❌ Ralat sistem. Sila cuba lagi.', 'bot');
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

        // Valid zakat types for reminders
        const validZakatTypes = [
            'pendapatan', 'simpanan', 'padi', 'saham', 'perak', 'kwsp',
            'income_kaedah_a', 'income_kaedah_b', 'savings', 'umum'
        ];

        const stateType = zakatTypeFromState !== null ? zakatTypeFromState : this.state.type;
        let zakatType = zakatTypeMap[stateType] || stateType;

        // Validate zakat type
        if (!zakatType || !validZakatTypes.includes(zakatType)) {
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