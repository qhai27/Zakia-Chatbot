// ===============================================
// FIXED ANALYTICS - WITH FORCED UI UPDATES
// ===============================================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('📊 Analytics script loading...');

        const CONFIG = {
            API_BASE: 'http://127.0.0.1:5000/admin/analytics',
            REFRESH_INTERVAL: 30000,
            CHART_COLORS: {
                primary: '#157347',
                secondary: '#5DB996',
                accent: '#FFD95F',
                danger: '#e53935'
            }
        };

        // Wait a bit for DOM to be fully ready
        setTimeout(() => {
            initializeAnalytics();
        }, 500);

        function initializeAnalytics() {
            console.log('🔧 Initializing analytics...');

            // Get all DOM elements
            const DOM = {
                analyticsSection: document.getElementById('analyticsSection'),
                periodSelector: document.getElementById('analyticsPeriod'),
                refreshBtn: document.getElementById('refreshAnalytics'),

                // Stats
                totalChats: document.getElementById('statTotalChats'),
                uniqueUsers: document.getElementById('statUniqueUsers'),
                avgSession: document.getElementById('statAvgSession'),
                growthRate: document.getElementById('statGrowthRate'),
                engagementScore: document.getElementById('statEngagement'),

                // Charts
                chatsChart: document.getElementById('chatsPerDayChart'),
                hourlyChart: document.getElementById('hourlyChart'),
                faqCategoriesChart: document.getElementById('faqCategoriesChart'),

                // Tables
                topQuestionsBody: document.getElementById('topQuestionsBody'),
                zakatPopularityBody: document.getElementById('zakatPopularityBody'),
                unansweredBody: document.getElementById('unansweredBody'),
                unansweredCount: document.getElementById('unansweredCount')
            };

            // Debug: Check what we found
            console.log('🔍 DOM Check:');
            Object.entries(DOM).forEach(([key, value]) => {
                console.log(`  ${key}:`, value ? '✅' : '❌ MISSING');
            });

            // Check for FAQ categories chart
            if (DOM.faqCategoriesChart) {
                console.log('  faqCategoriesChart: ✅');
            } else {
                console.warn('  faqCategoriesChart: ❌ MISSING');
            }

            let STATE = {
                currentPeriod: 'month',
                autoRefreshTimer: null,
                charts: { chatsPerDay: null, hourly: null, faqCategories: null }
            };

            // ===================================
            // API SERVICE
            // ===================================

            const APIService = {
                async fetchDashboard(period = 'month') {
                    console.log(`📡 Fetching dashboard: ${period}`);
                    const params = new URLSearchParams({ period });
                    const res = await fetch(`${CONFIG.API_BASE}/dashboard?${params}`);
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const data = await res.json();
                    console.log('📊 Dashboard data:', data);
                    return data;
                },

                async fetchUnanswered(status = 'new', limit = 10) {
                    console.log(`📡 Fetching unanswered: ${status}`);
                    const params = new URLSearchParams({ status, limit: limit.toString() });
                    const res = await fetch(`${CONFIG.API_BASE}/unanswered?${params}`);
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    const data = await res.json();
                    console.log('❓ Unanswered data:', data);
                    return data;
                }
            };

            // ===================================
            // UI MANAGER - FORCED UPDATES
            // ===================================

            const UIManager = {
                updateOverview(data) {
                    console.log('🎨 Updating overview UI...');
                    const overview = data.overview;

                    // Force update each stat with visibility check
                    if (DOM.totalChats) {
                        DOM.totalChats.textContent = overview.total_chats.toLocaleString();
                        DOM.totalChats.style.display = 'block';
                        DOM.totalChats.style.visibility = 'visible';
                        console.log('  ✅ Total chats updated:', overview.total_chats);
                    } else {
                        console.error('  ❌ totalChats element not found!');
                    }

                    if (DOM.uniqueUsers) {
                        DOM.uniqueUsers.textContent = overview.unique_users.toLocaleString();
                        DOM.uniqueUsers.style.display = 'block';
                        console.log('  ✅ Unique users updated:', overview.unique_users);
                    }

                    if (DOM.avgSession) {
                        DOM.avgSession.textContent = overview.avg_session_length.toFixed(1);
                        DOM.avgSession.style.display = 'block';
                        console.log('  ✅ Avg session updated:', overview.avg_session_length);
                    }

                    if (DOM.growthRate) {
                        const growth = overview.growth_rate;
                        const sign = growth >= 0 ? '+' : '';
                        DOM.growthRate.textContent = `${sign}${growth}%`;
                        DOM.growthRate.className = 'stat-value ' + (growth >= 0 ? 'stat-positive' : 'stat-negative');
                        console.log('  ✅ Growth rate updated:', growth);
                    }

                    if (DOM.engagementScore) {
                        DOM.engagementScore.textContent = overview.engagement_score.toFixed(1);
                        const scoreClass = this.getEngagementClass(overview.engagement_score);
                        DOM.engagementScore.className = 'stat-value ' + scoreClass;
                        console.log('  ✅ Engagement score updated:', overview.engagement_score);
                    }

                    console.log('✅ Overview UI updated!');
                },

                getEngagementClass(score) {
                    if (score >= 80) return 'score-excellent';
                    if (score >= 60) return 'score-good';
                    if (score >= 40) return 'score-fair';
                    return 'score-poor';
                },

                renderCharts(chatsData, hourlyData) {
                    console.log('📈 Rendering charts...');

                    // Chats per day
                    if (DOM.chatsChart && typeof Chart !== 'undefined') {
                        console.log('  📊 Creating chats chart...');
                        const labels = chatsData.map(d => this.formatDate(d.date));
                        const values = chatsData.map(d => d.count);

                        if (STATE.charts.chatsPerDay) {
                            STATE.charts.chatsPerDay.destroy();
                        }

                        const ctx = DOM.chatsChart.getContext('2d');
                        STATE.charts.chatsPerDay = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: labels,
                                datasets: [{
                                    label: 'Chats',
                                    data: values,
                                    borderColor: CONFIG.CHART_COLORS.primary,
                                    backgroundColor: `${CONFIG.CHART_COLORS.primary}20`,
                                    tension: 0.4,
                                    fill: true
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: { y: { beginAtZero: true } }
                            }
                        });
                        console.log('  ✅ Chats chart created');
                    } else {
                        console.warn('  ⚠️ Chart.js not available or canvas not found');
                    }

                    // Hourly distribution
                    if (DOM.hourlyChart && typeof Chart !== 'undefined') {
                        console.log('  📊 Creating hourly chart...');
                        const labels = hourlyData.map(d => `${d.hour}:00`);
                        const values = hourlyData.map(d => d.count);

                        if (STATE.charts.hourly) {
                            STATE.charts.hourly.destroy();
                        }

                        const ctx = DOM.hourlyChart.getContext('2d');
                        STATE.charts.hourly = new Chart(ctx, {
                            type: 'bar',
                            data: {
                                labels: labels,
                                datasets: [{
                                    label: 'Messages',
                                    data: values,
                                    backgroundColor: CONFIG.CHART_COLORS.secondary
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: { legend: { display: false } },
                                scales: { y: { beginAtZero: true } }
                            }
                        });
                        console.log('  ✅ Hourly chart created');
                    }
                },

                renderFaqCategoriesChart(categoriesData) {
                    console.log('📊 Rendering FAQ categories chart...', categoriesData);
                    console.log('📊 Categories data type:', typeof categoriesData, Array.isArray(categoriesData));

                    if (typeof Chart === 'undefined') {
                        console.error('  ❌ Chart.js library not loaded');
                        return;
                    }

                    if (!DOM.faqCategoriesChart) {
                        console.error('  ❌ FAQ categories chart canvas element not found');
                        return;
                    }

                    if (!categoriesData || categoriesData.length === 0) {
                        console.log('  ℹ️ No FAQ categories data to display');
                        // Show empty state message
                        const ctx = DOM.faqCategoriesChart.getContext('2d');
                        ctx.clearRect(0, 0, DOM.faqCategoriesChart.width, DOM.faqCategoriesChart.height);
                        ctx.font = '14px Arial';
                        ctx.fillStyle = '#9ca3af';
                        ctx.textAlign = 'center';
                        ctx.fillText('No FAQ data available', DOM.faqCategoriesChart.width / 2, DOM.faqCategoriesChart.height / 2);
                        return;
                    }

                    // Debug: Log first item structure
                    if (categoriesData.length > 0) {
                        console.log('  🔍 First item structure:', categoriesData[0]);
                        console.log('  🔍 First item keys:', Object.keys(categoriesData[0] || {}));
                    }

                    // Destroy existing chart if any
                    if (STATE.charts.faqCategories) {
                        STATE.charts.faqCategories.destroy();
                    }

                    // Handle different data structures
                    let labels, values;
                    if (categoriesData[0] && typeof categoriesData[0] === 'object') {
                        // Check if it's an array of objects with proper keys
                        const firstItem = categoriesData[0];
                        if ('category' in firstItem && 'count' in firstItem) {
                            labels = categoriesData.map(item => item.category || 'Umum');
                            values = categoriesData.map(item => Number(item.count) || 0);
                        } else if (Object.keys(firstItem).length > 0) {
                            // Try to extract from object keys
                            const keys = Object.keys(firstItem);
                            const categoryKey = keys.find(k => k.toLowerCase().includes('category') || k.toLowerCase().includes('cat'));
                            const countKey = keys.find(k => k.toLowerCase().includes('count') || k.toLowerCase().includes('num'));

                            if (categoryKey && countKey) {
                                labels = categoriesData.map(item => item[categoryKey] || 'Umum');
                                values = categoriesData.map(item => Number(item[countKey]) || 0);
                            } else {
                                console.error('  ❌ Could not find category/count keys in data:', keys);
                                return;
                            }
                        } else {
                            console.error('  ❌ Data objects are empty or malformed');
                            return;
                        }
                    } else {
                        console.error('  ❌ Unexpected data structure:', typeof categoriesData[0]);
                        return;
                    }

                    console.log('  📊 Extracted labels:', labels);
                    console.log('  📊 Extracted values:', values);

                    // Generate colors for pie chart
                    const colors = [
                        '#157347', '#5DB996', '#FFD95F', '#e53935',
                        '#2196F3', '#9C27B0', '#FF9800', '#00BCD4',
                        '#4CAF50', '#F44336', '#E91E63', '#673AB7'
                    ];

                    const backgroundColors = categoriesData.map((_, index) => {
                        return colors[index % colors.length];
                    });

                    const ctx = DOM.faqCategoriesChart.getContext('2d');

                    // Determine legend position based on screen size
                    const isMobile = window.innerWidth <= 768;
                    const isSmallMobile = window.innerWidth <= 480;

                    STATE.charts.faqCategories = new Chart(ctx, {
                        type: 'doughnut',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'FAQs',
                                data: values,
                                backgroundColor: backgroundColors,
                                borderColor: '#ffffff',
                                borderWidth: 2
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: {
                                    position: isSmallMobile ? 'bottom' : (isMobile ? 'bottom' : 'right'),
                                    labels: {
                                        padding: isSmallMobile ? 8 : 15,
                                        usePointStyle: true,
                                        font: {
                                            size: isSmallMobile ? 10 : (isMobile ? 11 : 12)
                                        },
                                        boxWidth: isSmallMobile ? 10 : 12,
                                        boxHeight: isSmallMobile ? 10 : 12
                                    }
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function (context) {
                                            const label = context.label || '';
                                            const value = context.parsed || 0;
                                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                            const percentage = ((value / total) * 100).toFixed(1);
                                            return `${label}: ${value} (${percentage}%)`;
                                        }
                                    }
                                }
                            }
                        }
                    });

                    // Update chart on window resize
                    let resizeTimer;
                    window.addEventListener('resize', () => {
                        clearTimeout(resizeTimer);
                        resizeTimer = setTimeout(() => {
                            if (STATE.charts.faqCategories) {
                                const isMobileNow = window.innerWidth <= 768;
                                const isSmallMobileNow = window.innerWidth <= 480;

                                STATE.charts.faqCategories.options.plugins.legend.position =
                                    isSmallMobileNow ? 'bottom' : (isMobileNow ? 'bottom' : 'right');
                                STATE.charts.faqCategories.options.plugins.legend.labels.font.size =
                                    isSmallMobileNow ? 10 : (isMobileNow ? 11 : 12);
                                STATE.charts.faqCategories.options.plugins.legend.labels.padding =
                                    isSmallMobileNow ? 8 : 15;

                                STATE.charts.faqCategories.update();
                            }
                        }, 250);
                    });

                    console.log('  ✅ FAQ categories chart created');
                },

                renderTopQuestions(questions) {
                    console.log('📝 Rendering top questions...', questions.length);
                    if (!DOM.topQuestionsBody) {
                        console.error('  ❌ topQuestionsBody not found!');
                        return;
                    }

                    if (questions.length === 0) {
                        DOM.topQuestionsBody.innerHTML = `
                            <tr><td colspan="2" class="text-center text-muted">Tiada data</td></tr>
                        `;
                        return;
                    }

                    DOM.topQuestionsBody.innerHTML = questions.map(q => `
                        <tr>
                            <td class="question-text">${this.escapeHtml(q.user_message)}</td>
                            <td class="text-center">
                                <span class="frequency-badge">${q.frequency}</span>
                            </td>
                        </tr>
                    `).join('');
                    console.log('  ✅ Top questions rendered');
                },

                renderZakatPopularity(data) {
                    console.log('💰 Rendering zakat popularity...', data.length);
                    if (!DOM.zakatPopularityBody) {
                        console.error('  ❌ zakatPopularityBody not found!');
                        return;
                    }

                    if (data.length === 0) {
                        DOM.zakatPopularityBody.innerHTML = `
                            <tr><td colspan="3" class="text-center text-muted">Tiada data</td></tr>
                        `;
                        return;
                    }

                    DOM.zakatPopularityBody.innerHTML = data.map(item => `
                        <tr>
                            <td>${this.formatZakatType(item.zakat_type)}</td>
                            <td class="text-center">${item.count}</td>
                            <td class="text-right">RM ${parseFloat(item.total_amount || 0).toFixed(2)}</td>
                        </tr>
                    `).join('');
                    console.log('  ✅ Zakat popularity rendered');
                },

                renderFaqAnalytics(faqData) {
                    console.log('📋 Rendering FAQ analytics...', faqData);

                    // Update FAQ stats cards if they exist
                    const totalFaqsEl = document.getElementById('faqStatTotal');
                    const recentFaqsEl = document.getElementById('faqStatRecent');
                    const avgLengthEl = document.getElementById('faqStatAvgLength');
                    const topCategoryEl = document.getElementById('faqStatTopCategory');

                    if (totalFaqsEl) {
                        totalFaqsEl.textContent = faqData.total_faqs || 0;
                        console.log(`  ✅ Total FAQs updated: ${faqData.total_faqs || 0}`);
                    } else {
                        console.warn('  ⚠️ faqStatTotal element not found');
                    }

                    if (recentFaqsEl) {
                        recentFaqsEl.textContent = faqData.recent_faqs || 0;
                        console.log(`  ✅ Recent FAQs updated: ${faqData.recent_faqs || 0}`);
                    } else {
                        console.warn('  ⚠️ faqStatRecent element not found');
                    }

                    if (avgLengthEl) {
                        const avgLength = Math.round(faqData.avg_answer_length || 0);
                        avgLengthEl.textContent = `${avgLength} chars`;
                        console.log(`  ✅ Avg answer length updated: ${avgLength} chars`);
                    } else {
                        console.warn('  ⚠️ faqStatAvgLength element not found');
                    }

                    if (topCategoryEl) {
                        if (faqData.top_categories && faqData.top_categories.length > 0) {
                            const top = faqData.top_categories[0];
                            topCategoryEl.textContent = `${top.category} (${top.count})`;
                            console.log(`  ✅ Top category updated: ${top.category} (${top.count})`);
                        } else {
                            topCategoryEl.textContent = '-';
                            console.log('  ℹ️ No top category data available');
                        }
                    } else {
                        console.warn('  ⚠️ faqStatTopCategory element not found');
                    }

                    // Render FAQ categories table
                    const faqCategoriesBody = document.getElementById('faqCategoriesBody');
                    if (faqCategoriesBody) {
                        if (!faqData.faqs_by_category || faqData.faqs_by_category.length === 0) {
                            faqCategoriesBody.innerHTML = `
                                <tr><td colspan="2" class="text-center text-muted">Tiada data</td></tr>
                            `;
                            console.log('  ℹ️ No FAQ categories data to display');
                        } else {
                            faqCategoriesBody.innerHTML = faqData.faqs_by_category.map(item => `
                                <tr>
                                    <td>${this.escapeHtml(item.category || 'Umum')}</td>
                                    <td class="text-center">
                                        <span class="frequency-badge">${item.count}</span>
                                    </td>
                                </tr>
                            `).join('');
                            console.log(`  ✅ FAQ categories rendered: ${faqData.faqs_by_category.length} categories`);
                        }
                    } else {
                        console.warn('  ⚠️ faqCategoriesBody element not found');
                    }

                    console.log('  ✅ FAQ analytics rendered');
                },

                renderUnansweredQuestions(questions) {
                    console.log('❓ Rendering unanswered questions...', questions.length);

                    if (DOM.unansweredCount) {
                        DOM.unansweredCount.textContent = questions.length;
                    }

                    if (!DOM.unansweredBody) return;

                    if (questions.length === 0) {
                        DOM.unansweredBody.innerHTML = `
                            <tr><td colspan="4" class="text-center text-muted">✅ Tiada soalan tidak dijawab</td></tr>
                        `;
                        return;
                    }

                    DOM.unansweredBody.innerHTML = questions.map(q => `
                        <tr>
                            <td>${q.id}</td>
                            <td>${this.escapeHtml(q.question)}</td>
                            <td class="text-center">
                                <span class="confidence-badge">${(q.confidence_score * 100).toFixed(0)}%</span>
                            </td>
                            <td>
                                <button class="btn btn-sm primary convert-to-faq-btn" data-id="${q.id}" data-question="${this.escapeHtml(q.question)}" title="Convert to FAQ">
                                    ➕ Convert to FAQ
                                </button>
                            </td>
                        </tr>
                    `).join('');

                    // Attach event listeners to convert buttons
                    DOM.unansweredBody.querySelectorAll('.convert-to-faq-btn').forEach(btn => {
                        btn.addEventListener('click', (e) => {
                            const questionId = btn.getAttribute('data-id');
                            const question = btn.getAttribute('data-question');
                            this.showConvertToFaqModal(questionId, question);
                        });
                    });

                    console.log('  ✅ Unanswered questions rendered');
                },

                showConvertToFaqModal(questionId, question) {
                    // Remove existing modal if any
                    const existing = document.getElementById('convertToFaqModal');
                    if (existing) existing.remove();

                    const modal = document.createElement('div');
                    modal.id = 'convertToFaqModal';
                    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000;';
                    modal.innerHTML = `
                        <div style="width:600px;max-width:90vw;background:#fff;border-radius:12px;padding:24px;box-shadow:0 10px 40px rgba(0,0,0,0.2);max-height:90vh;overflow-y:auto;">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                                <h3 style="margin:0;color:#157347;">➕ Convert to FAQ</h3>
                                <button class="btn-close" onclick="this.closest('#convertToFaqModal').remove()">✖</button>
                            </div>
                            
                            <div style="margin-bottom:16px;padding:12px;background:#f8f9fa;border-radius:8px;">
                                <strong>Question:</strong>
                                <p style="margin:8px 0 0 0;color:#495057;">${question}</p>
                            </div>
                            
                            <div style="margin-bottom:16px;">
                                <label style="display:block;margin-bottom:8px;font-weight:600;">Answer <span style="color:#e53e3e;">*</span></label>
                                <textarea id="convertFaqAnswer" rows="6" style="width:100%;padding:10px;border:1px solid #ddd;border-radius:6px;font-family:inherit;resize:vertical;" placeholder="Masukkan jawapan untuk soalan ini..."></textarea>
                            </div>
                            
                            <div style="margin-bottom:20px;">
                                <label style="display:block;margin-bottom:8px;font-weight:600;">Category</label>
                                <input id="convertFaqCategory" type="text" style="width:100%;padding:10px;border:1px solid #ddd;border-radius:6px;" placeholder="Umum" value="Umum">
                                <small style="color:#6c757d;display:block;margin-top:4px;">Kosongkan untuk menggunakan kategori "Umum"</small>
                            </div>
                            
                            <div id="convertFaqMessage" style="display:none;padding:12px;border-radius:6px;margin-bottom:16px;"></div>
                            
                            <div style="display:flex;justify-content:flex-end;gap:12px;">
                                <button class="btn ghost" onclick="document.getElementById('convertToFaqModal').remove()">Batal</button>
                                <button id="convertFaqSubmitBtn" class="btn primary">💾 Convert to FAQ</button>
                            </div>
                        </div>
                    `;

                    document.body.appendChild(modal);

                    // Close on overlay click
                    modal.addEventListener('click', (e) => {
                        if (e.target === modal) modal.remove();
                    });

                    // Handle submit
                    const submitBtn = document.getElementById('convertFaqSubmitBtn');
                    const answerInput = document.getElementById('convertFaqAnswer');
                    const categoryInput = document.getElementById('convertFaqCategory');
                    const messageDiv = document.getElementById('convertFaqMessage');

                    submitBtn.addEventListener('click', async () => {
                        const answer = answerInput.value.trim();
                        const category = categoryInput.value.trim() || 'Umum';

                        if (!answer) {
                            messageDiv.style.display = 'block';
                            messageDiv.style.background = '#fee';
                            messageDiv.style.color = '#c33';
                            messageDiv.textContent = '❌ Sila masukkan jawapan.';
                            return;
                        }

                        submitBtn.disabled = true;
                        submitBtn.textContent = '⏳ Converting...';
                        messageDiv.style.display = 'none';

                        try {
                            const response = await fetch(`${CONFIG.API_BASE}/unanswered/${questionId}/convert-to-faq`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ answer, category })
                            });

                            const data = await response.json();

                            if (data.success) {
                                messageDiv.style.display = 'block';
                                messageDiv.style.background = '#d4edda';
                                messageDiv.style.color = '#155724';
                                messageDiv.textContent = '✅ Berjaya ditukar kepada FAQ!';

                                // Reload analytics after 1 second
                                setTimeout(() => {
                                    modal.remove();
                                    if (window.AnalyticsOperations) {
                                        AnalyticsOperations.loadDashboard(STATE.currentPeriod);
                                    }
                                }, 1500);
                            } else {
                                messageDiv.style.display = 'block';
                                messageDiv.style.background = '#fee';
                                messageDiv.style.color = '#c33';
                                messageDiv.textContent = `❌ ${data.error || 'Gagal menukar kepada FAQ'}`;
                                submitBtn.disabled = false;
                                submitBtn.textContent = '💾 Convert to FAQ';
                            }
                        } catch (error) {
                            messageDiv.style.display = 'block';
                            messageDiv.style.background = '#fee';
                            messageDiv.style.color = '#c33';
                            messageDiv.textContent = `❌ Error: ${error.message}`;
                            submitBtn.disabled = false;
                            submitBtn.textContent = '💾 Convert to FAQ';
                        }
                    });

                    // Focus answer input
                    answerInput.focus();
                },

                formatZakatType(type) {
                    const map = {
                        'pendapatan': 'Pendapatan', 'simpanan': 'Simpanan',
                        'padi': 'Padi', 'saham': 'Saham',
                        'perak': 'Perak', 'kwsp': 'KWSP'
                    };
                    return map[type] || type;
                },

                formatDate(dateStr) {
                    const date = new Date(dateStr);
                    return date.toLocaleDateString('ms-MY', { day: '2-digit', month: 'short' });
                },

                escapeHtml(str) {
                    return (str || '').replace(/[&<>"']/g, m => ({
                        '&': '&amp;', '<': '&lt;', '>': '&gt;',
                        '"': '&quot;', "'": '&#039;'
                    })[m]);
                }
            };

            // ===================================
            // OPERATIONS
            // ===================================

            const AnalyticsOperations = {
                async loadDashboard(period = 'month') {
                    try {
                        console.log(`\n📊 ========== LOADING ANALYTICS (${period}) ==========`);

                        const [dashboardData, unansweredData] = await Promise.all([
                            APIService.fetchDashboard(period),
                            APIService.fetchUnanswered('new', 10)
                        ]);

                        if (dashboardData.success) {
                            console.log('✅ Dashboard data received successfully');
                            UIManager.updateOverview(dashboardData);
                            UIManager.renderCharts(
                                dashboardData.charts.chats_per_day,
                                dashboardData.charts.hourly_distribution
                            );
                            UIManager.renderTopQuestions(dashboardData.top_questions);
                            UIManager.renderZakatPopularity(dashboardData.zakat_popularity);

                            // Render FAQ analytics if available
                            if (dashboardData.faq_analytics) {
                                UIManager.renderFaqAnalytics(dashboardData.faq_analytics);
                                // Render FAQ categories chart
                                if (dashboardData.faq_analytics.faqs_by_category) {
                                    UIManager.renderFaqCategoriesChart(dashboardData.faq_analytics.faqs_by_category);
                                }
                            }
                        } else {
                            console.error('❌ Dashboard data failed:', dashboardData);
                        }

                        if (unansweredData.success) {
                            console.log('✅ Unanswered data received successfully');
                            UIManager.renderUnansweredQuestions(unansweredData.questions);
                        }

                        console.log('✅ ========== ANALYTICS LOADED ==========\n');

                    } catch (error) {
                        console.error('❌ ERROR LOADING ANALYTICS:', error);
                        alert(`Failed to load analytics:\n${error.message}`);
                    }
                }
            };

            // ===================================
            // EVENT LISTENERS
            // ===================================

            if (DOM.periodSelector) {
                DOM.periodSelector.addEventListener('change', (e) => {
                    STATE.currentPeriod = e.target.value;
                    AnalyticsOperations.loadDashboard(STATE.currentPeriod);
                });
            }

            if (DOM.refreshBtn) {
                DOM.refreshBtn.addEventListener('click', () => {
                    AnalyticsOperations.loadDashboard(STATE.currentPeriod);
                });
            }

            // ===================================
            // NAVIGATION HANDLER
            // Navigation is handled by admin-navigation.js
            // This section-specific handler only loads data when analytics section is shown
            // ===================================

            const analyticsNav = document.querySelector('[data-section="analytics"]');
            if (analyticsNav) {
                console.log('✅ Analytics nav found, attaching listener');
                analyticsNav.addEventListener('click', () => {
                    console.log('🎯 Analytics nav clicked!');
                    // Navigation handler will show the section
                    // We just need to load the data
                    setTimeout(() => {
                        AnalyticsOperations.loadDashboard(STATE.currentPeriod);
                    }, 300);
                });
            } else {
                console.warn('⚠️ Analytics nav item not found');
            }

            // Make globally accessible
            window.AnalyticsOperations = AnalyticsOperations;

            console.log('✅ Analytics initialized');
        }
    });
})();