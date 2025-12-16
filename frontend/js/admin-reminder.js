// =========================
// ADMIN REMINDERS HANDLER
// =========================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const CONFIG = {
            API_BASE: 'http://127.0.0.1:5000/admin/reminders',
            STATS_API: 'http://127.0.0.1:5000/admin/reminders/stats',
            CHATLOG_API: 'http://127.0.0.1:5000/admin/chat-logs',
            PAGE_SIZE: 20
        };

        const DOM = {
            reminderTableBody: document.getElementById('reminderTableBody'),
            reminderEmptyState: document.getElementById('reminderEmptyState'),
            reminderSearch: document.getElementById('reminderSearch'),
            zakatTypeFilter: document.getElementById('zakatTypeFilter'),
            refreshReminders: document.getElementById('refreshReminders'),
            reminderStatus: document.getElementById('reminderStatus'),
            reminderPagination: document.getElementById('reminderPagination'),
            printRemindersBtn: document.getElementById('printRemindersBtn'),
            exportRemindersBtn: document.getElementById('exportRemindersBtn'),
            statsTotal: document.getElementById('statsTotal'),
            statsTotalAmount: document.getElementById('statsTotalAmount'),
            statsPendapatan: document.getElementById('statsPendapatan'),
            statsSimpanan: document.getElementById('statsSimpanan'),
            statsPadi: document.getElementById('statsPadi'),
            statsSaham: document.getElementById('statsSaham'),
            statsPerak: document.getElementById('statsPerak'),
            statsKwsp: document.getElementById('statsKwsp'),
            totalReminders: document.getElementById('totalReminders'),
            // Chat log DOM elements
            chatlogTableBody: document.getElementById('chatlogTableBody'),
            chatlogEmptyState: document.getElementById('chatlogEmptyState'),
            chatlogStatus: document.getElementById('chatlogStatus'),
            refreshChatLogs: document.getElementById('refreshChatLogs')
        };

        let STATE = {
            reminders: [],
            filteredReminders: [],
            currentPage: 1,
            totalPages: 1,
            isLoading: false,
            stats: null
        };

        // Navigation Handler
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('data-section');

                // Update active nav
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');

                // Show appropriate section
                document.querySelectorAll('.content-section').forEach(sec => {
                    sec.style.display = 'none';
                });

                if (section === 'reminders') {
                    document.getElementById('remindersSection').style.display = 'block';
                    ReminderOperations.load();
                } else if (section === 'faqs') {
                    document.getElementById('faqSection').style.display = 'block';
                } else if (section === 'chatlog') {
                    document.getElementById('chatlogSection').style.display = 'block';
                    ChatLogOperations.load();
                }
            });
        });

        const UIManager = {
            updateStatus(message, isError = false) {
                if (DOM.reminderStatus) {
                    DOM.reminderStatus.textContent = message;
                    DOM.reminderStatus.style.color = isError ? '#e53e3e' : '#718096';
                }
            },

            showLoading(show = true) {
                STATE.isLoading = show;
                if (DOM.refreshReminders) {
                    DOM.refreshReminders.disabled = show;
                    DOM.refreshReminders.innerHTML = show ? '⏳ Memuat...' : '🔄 Refresh';
                }
            },

            escapeHtml(str) {
                return (str || '')
                    .replaceAll('&', '&amp;')
                    .replaceAll('<', '&lt;')
                    .replaceAll('>', '&gt;');
            },

            formatDate(dateStr) {
                if (!dateStr) return 'N/A';
                const date = new Date(dateStr);
                return date.toLocaleDateString('ms-MY', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric'
                });
            },

            formatAmount(amount) {
                if (!amount) return 'RM 0.00';
                return `RM ${parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
            },

            formatIC(ic) {
                if (!ic) return '';
                // Format IC as 123456-12-1234
                if (ic.length === 12) {
                    return `${ic.substr(0, 6)}-${ic.substr(6, 2)}-${ic.substr(8, 4)}`;
                }
                return ic;
            },

            formatPhone(phone) {
                if (!phone) return '';
                // Format phone as 012-345 6789
                if (phone.length >= 10) {
                    return `${phone.substr(0, 3)}-${phone.substr(3, 3)} ${phone.substr(6)}`;
                }
                return phone;
            },

            formatZakatType(zakatType) {
                if (!zakatType) return 'N/A';

                // Map zakat types to display names
                const typeMap = {
                    'pendapatan': 'Pendapatan',
                    'income_kaedah_a': 'Pendapatan (Kaedah A)',
                    'income_kaedah_b': 'Pendapatan (Kaedah B)',
                    'simpanan': 'Simpanan',
                    'savings': 'Simpanan',
                    'padi': 'Padi',
                    'saham': 'Saham',
                    'perak': 'Perak',
                    'kwsp': 'KWSP',
                    'umum': 'Umum'
                };

                // Check if we have a mapped name
                if (typeMap[zakatType]) {
                    return typeMap[zakatType];
                }

                // Fallback: capitalize first letter and handle underscores
                return zakatType
                    .split('_')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                    .join(' ');
            },

            getZakatTypeIcon(zakatType) {
                if (!zakatType) return '💰';

                const iconMap = {
                    'pendapatan': '💼',
                    'income_kaedah_a': '💼',
                    'income_kaedah_b': '💼',
                    'simpanan': '💰',
                    'savings': '💰',
                    'padi': '🌾',
                    'saham': '📈',
                    'perak': '🥈',
                    'kwsp': '🏦',
                    'umum': '💰'
                };

                return iconMap[zakatType] || '💰';
            },

            formatYear(year) {
                if (!year) return 'N/A';
                // Year should already be in format "2025 Masihi" or "1446 Hijrah"
                // Just return it as is, or format if needed
                return year.trim();
            },

            renderReminders(reminders) {
                if (!DOM.reminderTableBody) return;

                if (reminders.length === 0) {
                    DOM.reminderTableBody.innerHTML = '';
                    if (DOM.reminderEmptyState) DOM.reminderEmptyState.style.display = 'block';
                    return;
                }

                if (DOM.reminderEmptyState) DOM.reminderEmptyState.style.display = 'none';

                DOM.reminderTableBody.innerHTML = reminders.map(r => `
                    <tr>
                        <td><span class="id-badge">#${r.id_reminder}</span></td>
                        <td><strong>${this.escapeHtml(r.name)}</strong></td>
                        <td><code>${this.formatIC(r.ic_number)}</code></td>
                        <td><code>${this.formatPhone(r.phone)}</code></td>
                        <td>
                            <span class="zakat-type-badge ${r.zakat_type || 'umum'}">
                                ${this.getZakatTypeIcon(r.zakat_type)} 
                                ${this.escapeHtml(this.formatZakatType(r.zakat_type))}
                            </span>
                        </td>
                        <td class="amount-cell">${this.formatAmount(r.zakat_amount)}</td>
                        <td class="year-cell">${this.escapeHtml(this.formatYear(r.year))}</td>
                        <td class="date-cell">${this.formatDate(r.created_at)}</td>
                        <td>
                            <div class="admin-actions">
                                <button class="btn ghost btn-sm" data-action="view" data-id="${r.id_reminder}" title="Papar Butiran">
                                    👁️ Papar
                                </button>
                                <button class="btn warn btn-sm" data-action="delete" data-id="${r.id_reminder}" title="Padam">
                                    🗑️
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            },

            renderPagination(currentPage, totalPages) {
                if (!DOM.reminderPagination || totalPages <= 1) {
                    if (DOM.reminderPagination) DOM.reminderPagination.innerHTML = '';
                    return;
                }

                const pages = [];
                const maxVisible = 5;
                let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
                let endPage = Math.min(totalPages, startPage + maxVisible - 1);

                if (endPage - startPage < maxVisible - 1) {
                    startPage = Math.max(1, endPage - maxVisible + 1);
                }

                if (currentPage > 1) {
                    pages.push(`<button class="page-btn" data-page="${currentPage - 1}">‹ Prev</button>`);
                }

                for (let i = startPage; i <= endPage; i++) {
                    const active = i === currentPage ? 'active' : '';
                    pages.push(`<button class="page-btn ${active}" data-page="${i}">${i}</button>`);
                }

                if (currentPage < totalPages) {
                    pages.push(`<button class="page-btn" data-page="${currentPage + 1}">Next ›</button>`);
                }

                DOM.reminderPagination.innerHTML = `
                    <div class="pagination-info">
                        Page ${currentPage} of ${totalPages} (${STATE.filteredReminders.length} reminders)
                    </div>
                    <div class="pagination-buttons">
                        ${pages.join('')}
                    </div>
                `;

                // Attach pagination listeners
                DOM.reminderPagination.querySelectorAll('.page-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const page = parseInt(btn.getAttribute('data-page'));
                        ReminderOperations.changePage(page);
                    });
                });
            },

            updateStats(stats) {
                if (!stats) return;

                // Update total reminders
                if (DOM.statsTotal) {
                    DOM.statsTotal.textContent = stats.total || 0;
                }
                if (DOM.totalReminders) {
                    DOM.totalReminders.textContent = stats.total || 0;
                }

                // Update total amount
                if (DOM.statsTotalAmount) {
                    DOM.statsTotalAmount.textContent = this.formatAmount(stats.total_amount);
                }

                // Update by type
                const byType = stats.by_type || [];
                let pendapatanCount = 0;
                let simpananCount = 0;
                let padiCount = 0;
                let sahamCount = 0;
                let perakCount = 0;
                let kwspCount = 0;

                byType.forEach(item => {
                    const type = item.zakat_type || '';
                    const count = item.count || 0;
                    if (type === 'pendapatan') {
                        pendapatanCount = count;
                    } else if (type === 'simpanan') {
                        simpananCount = count;
                    } else if (type === 'padi') {
                        padiCount = count;
                    } else if (type === 'saham') {
                        sahamCount = count;
                    } else if (type === 'perak') {
                        perakCount = count;
                    } else if (type === 'kwsp') {
                        kwspCount = count;
                    }
                });

                if (DOM.statsPendapatan) {
                    DOM.statsPendapatan.textContent = pendapatanCount;
                }
                if (DOM.statsSimpanan) {
                    DOM.statsSimpanan.textContent = simpananCount;
                }
                if (DOM.statsPadi) {
                    DOM.statsPadi.textContent = padiCount;
                }
                if (DOM.statsSaham) {
                    DOM.statsSaham.textContent = sahamCount;
                }
                if (DOM.statsPerak) {
                    DOM.statsPerak.textContent = perakCount;
                }
                if (DOM.statsKwsp) {
                    DOM.statsKwsp.textContent = kwspCount;
                }

                // Animate stats
                [DOM.statsTotal, DOM.statsTotalAmount, DOM.statsPendapatan, DOM.statsSimpanan,
                DOM.statsPadi, DOM.statsSaham, DOM.statsPerak, DOM.statsKwsp].forEach(el => {
                    if (el) {
                        el.style.transform = 'scale(1.15)';
                        setTimeout(() => {
                            el.style.transform = 'scale(1)';
                        }, 200);
                    }
                });
            }
        };

        const ChatLogUI = {
            updateStatus(message, isError = false) {
                if (DOM.chatlogStatus) {
                    DOM.chatlogStatus.textContent = message;
                    DOM.chatlogStatus.style.color = isError ? '#e53e3e' : '#718096';
                }
            },

            renderLogs(logs) {
                if (!DOM.chatlogTableBody) return;

                if (!logs || logs.length === 0) {
                    DOM.chatlogTableBody.innerHTML = '';
                    if (DOM.chatlogEmptyState) DOM.chatlogEmptyState.style.display = 'block';
                    return;
                }

                if (DOM.chatlogEmptyState) DOM.chatlogEmptyState.style.display = 'none';

                DOM.chatlogTableBody.innerHTML = logs
                    .map(log => {
                        const created = log.created_at
                            ? new Date(log.created_at).toLocaleString('ms-MY', {
                                day: '2-digit',
                                month: 'short',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            })
                            : 'N/A';
                        const session = log.session_id || '-';
                        const userId = log.id_user != null ? `#${log.id_user}` : '-';
                        const userMsg = (log.user_message || '').replace(/\s+/g, ' ').trim();
                        const botMsg = (log.bot_response || '').replace(/\s+/g, ' ').trim();

                        return `
                            <tr>
                                <td><span class="id-badge">#${log.id_log}</span></td>
                                <td>${userId}</td>
                                <td><code>${session}</code></td>
                                <td class="chatlog-user">${UIManager.escapeHtml(userMsg)}</td>
                                <td class="chatlog-bot">${UIManager.escapeHtml(botMsg)}</td>
                                <td>${created}</td>
                            </tr>
                        `;
                    })
                    .join('');
            }
        };

        const APIService = {
            async fetchReminders(limit = 1000, offset = 0, search = '', zakatType = '') {
                const params = new URLSearchParams({
                    limit: limit.toString(),
                    offset: offset.toString()
                });

                if (search) params.append('search', search);
                if (zakatType) params.append('zakat_type', zakatType);

                const res = await fetch(`${CONFIG.API_BASE}?${params}`);

                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    const errorMsg = errorData.error || `HTTP ${res.status}: ${res.statusText}`;
                    throw new Error(errorMsg);
                }

                const data = await res.json();

                // Ensure response has expected structure
                if (!data.hasOwnProperty('reminders')) {
                    console.warn('Unexpected response format:', data);
                    return { reminders: [], count: 0 };
                }

                return data;
            },

            async fetchStats() {
                try {
                    const res = await fetch(CONFIG.STATS_API);

                    if (!res.ok) {
                        const errorData = await res.json().catch(() => ({}));
                        const errorMsg = errorData.error || `HTTP ${res.status}: ${res.statusText}`;
                        throw new Error(errorMsg);
                    }

                    const data = await res.json();

                    // Ensure response has expected structure
                    if (!data.hasOwnProperty('stats')) {
                        console.warn('Unexpected stats response format:', data);
                        return { stats: null };
                    }

                    return data;
                } catch (error) {
                    console.error('Error fetching stats:', error);
                    // Return default stats instead of throwing
                    return { stats: { total: 0, total_amount: 0, by_type: [] } };
                }
            },

            async deleteReminder(id) {
                const res = await fetch(`${CONFIG.API_BASE}/${id}`, {
                    method: 'DELETE'
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                return await res.json();
            },

            async getReminder(id) {
                const res = await fetch(`${CONFIG.API_BASE}/${id}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                return await res.json();
            },

            async fetchChatLogs(limit = 200, offset = 0) {
                const params = new URLSearchParams({
                    limit: limit.toString(),
                    offset: offset.toString()
                });

                const res = await fetch(`${CONFIG.CHATLOG_API}?${params}`);

                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    const errorMsg = errorData.error || `HTTP ${res.status}: ${res.statusText}`;
                    throw new Error(errorMsg);
                }

                const data = await res.json();
                if (!data.hasOwnProperty('logs')) {
                    console.warn('Unexpected chat log response format:', data);
                    return { logs: [], count: 0, total: 0 };
                }

                return data;
            }
        };

        const ReminderOperations = {
            async load() {
                try {
                    UIManager.showLoading(true);
                    UIManager.updateStatus('⏳ Memuat reminders...');

                    // Load reminders and stats separately to handle partial failures
                    let reminderData = { reminders: [], count: 0 };
                    let statsData = { stats: null };

                    try {
                        reminderData = await APIService.fetchReminders();
                    } catch (reminderError) {
                        console.error('Error fetching reminders:', reminderError);
                        UIManager.updateStatus(`⚠️ Gagal memuat reminders: ${reminderError.message}`, true);
                    }

                    try {
                        statsData = await APIService.fetchStats();
                    } catch (statsError) {
                        console.error('Error fetching stats:', statsError);
                        // Stats error is less critical, just log it
                    }

                    STATE.reminders = reminderData.reminders || [];
                    STATE.stats = statsData.stats || null;

                    this.applyFilters();
                    UIManager.updateStats(STATE.stats);

                    if (STATE.reminders.length > 0) {
                        UIManager.updateStatus(`✅ ${STATE.reminders.length} reminders loaded`);
                    } else {
                        UIManager.updateStatus('ℹ️ Tiada reminders ditemui', false);
                    }
                } catch (error) {
                    console.error('Error loading reminders:', error);
                    UIManager.updateStatus(`❌ Error: ${error.message}`, true);
                    STATE.reminders = [];
                    STATE.stats = null;
                    this.applyFilters();
                } finally {
                    UIManager.showLoading(false);
                }
            },

            applyFilters() {
                const search = (DOM.reminderSearch?.value || '').toLowerCase();
                const zakatType = DOM.zakatTypeFilter?.value || '';

                STATE.filteredReminders = STATE.reminders.filter(r => {
                    const matchesSearch = !search ||
                        (r.name && r.name.toLowerCase().includes(search)) ||
                        (r.ic_number && r.ic_number.includes(search)) ||
                        (r.phone && r.phone.includes(search));

                    // Normalize zakat types for matching
                    const normalizeType = (type) => {
                        if (!type) return '';
                        // Map variations to standard types for filtering
                        const typeMap = {
                            'income_kaedah_a': 'pendapatan',
                            'income_kaedah_b': 'pendapatan',
                            'savings': 'simpanan'
                        };
                        return typeMap[type] || type;
                    };

                    const reminderType = normalizeType(r.zakat_type);
                    const filterType = normalizeType(zakatType);
                    const matchesType = !zakatType || reminderType === filterType || r.zakat_type === zakatType;

                    return matchesSearch && matchesType;
                });

                STATE.totalPages = Math.ceil(STATE.filteredReminders.length / CONFIG.PAGE_SIZE);
                STATE.currentPage = 1;
                this.renderCurrentPage();
            },

            renderCurrentPage() {
                const startIdx = (STATE.currentPage - 1) * CONFIG.PAGE_SIZE;
                const endIdx = startIdx + CONFIG.PAGE_SIZE;
                const pageReminders = STATE.filteredReminders.slice(startIdx, endIdx);

                UIManager.renderReminders(pageReminders);
                UIManager.renderPagination(STATE.currentPage, STATE.totalPages);
            },

            changePage(page) {
                if (page < 1 || page > STATE.totalPages) return;
                STATE.currentPage = page;
                this.renderCurrentPage();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            },

            async delete(id, name) {
                const confirmed = confirm(
                    `⚠️ Delete reminder for ${name}?\n\nThis action cannot be undone.`
                );
                if (!confirmed) return;

                try {
                    UIManager.showLoading(true);
                    await APIService.deleteReminder(id);
                    UIManager.updateStatus('✅ Reminder deleted successfully');
                    await this.load();
                } catch (error) {
                    console.error('Delete error:', error);
                    UIManager.updateStatus(`❌ Failed to delete: ${error.message}`, true);
                } finally {
                    UIManager.showLoading(false);
                }
            },

            async viewDetails(id) {
                try {
                    const data = await APIService.getReminder(id);
                    if (data.success && data.reminder) {
                        this.showDetailModal(data.reminder);
                    }
                } catch (error) {
                    console.error('Error fetching reminder details:', error);
                    alert('Failed to load reminder details');
                }
            },

            showDetailModal(reminder) {
                const modal = document.getElementById('reminderDetailModal');
                const body = document.getElementById('reminderDetailBody');

                body.innerHTML = `
                    <div class="reminder-detail-card">
                        <div class="detail-header">
                            <h2>${UIManager.escapeHtml(reminder.name)}</h2>
                            <span class="zakat-type-badge ${reminder.zakat_type}">
                                ${UIManager.getZakatTypeIcon(reminder.zakat_type)} 
                                ${UIManager.escapeHtml(UIManager.formatZakatType(reminder.zakat_type))}
                            </span>
                        </div>
                        
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>ID:</label>
                                <span class="id-badge">#${reminder.id_reminder}</span>
                            </div>
                            <div class="detail-item">
                                <label>Nombor IC:</label>
                                <code>${UIManager.formatIC(reminder.ic_number)}</code>
                            </div>
                            <div class="detail-item">
                                <label>Telefon:</label>
                                <code>${UIManager.formatPhone(reminder.phone)}</code>
                            </div>
                            <div class="detail-item">
                                <label>Jenis Zakat:</label>
                                <span>${UIManager.escapeHtml(UIManager.formatZakatType(reminder.zakat_type))}</span>
                            </div>
                            <div class="detail-item">
                                <label>Tahun:</label>
                                <span>${UIManager.escapeHtml(UIManager.formatYear(reminder.year))}</span>
                            </div>
                            <div class="detail-item highlight">
                                <label>Jumlah Zakat:</label>
                                <strong>${UIManager.formatAmount(reminder.zakat_amount)}</strong>
                            </div>
                            <div class="detail-item">
                                <label>Tarikh Daftar:</label>
                                <span>${UIManager.formatDate(reminder.created_at)}</span>
                            </div>
                        </div>
                    </div>
                `;

                modal.style.display = 'flex';

                // Print single reminder
                const printBtn = document.getElementById('printSingleReminder');
                printBtn.onclick = () => PrintManager.printSingle(reminder);
            },

            exportCSV() {
                if (STATE.filteredReminders.length === 0) {
                    alert('No reminders to export');
                    return;
                }

                const headers = ['ID', 'Name', 'IC Number', 'Phone', 'Jenis Zakat', 'Zakat Amount', 'Tahun', 'Tarikh Daftar'];
                const rows = STATE.filteredReminders.map(r => [
                    r.id_reminder,
                    r.name,
                    r.ic_number,
                    r.phone,
                    UIManager.formatZakatType(r.zakat_type),
                    r.zakat_amount || 0,
                    UIManager.formatYear(r.year),
                    r.created_at || ''
                ]);

                const csvContent = [
                    headers.join(','),
                    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
                ].join('\n');

                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);

                link.setAttribute('href', url);
                link.setAttribute('download', `reminders_${new Date().toISOString().split('T')[0]}.csv`);
                link.style.visibility = 'hidden';

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        };

        const ChatLogOperations = {
            async load() {
                try {
                    ChatLogUI.updateStatus('⏳ Memuat chat log...');
                    const data = await APIService.fetchChatLogs();
                    ChatLogUI.renderLogs(data.logs || []);
                    if (data.total !== undefined) {
                        ChatLogUI.updateStatus(`✅ ${data.total} rekod chat log ditemui`);
                    } else {
                        ChatLogUI.updateStatus(`✅ ${data.logs?.length || 0} rekod chat log dimuatkan`);
                    }
                } catch (error) {
                    console.error('Error loading chat logs:', error);
                    ChatLogUI.updateStatus(`❌ Gagal memuat chat log: ${error.message}`, true);
                    ChatLogUI.renderLogs([]);
                }
            }
        };

        const PrintManager = {
            showFilterModal() {
                // Create modal if doesn't exist
                let modal = document.getElementById('printReminderFilterModal');
                if (!modal) {
                    modal = this.createFilterModal();
                    document.body.appendChild(modal);
                }

                // Populate filter options
                this.populateZakatTypeOptions();
                this.populateYearOptions();
                this.populateMonthOptions();

                modal.style.display = 'flex';
            },

            createFilterModal() {
                const modal = document.createElement('div');
                modal.id = 'printReminderFilterModal';
                modal.className = 'modal';
                modal.innerHTML = `
                    <div class="modal-overlay"></div>
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>🖨️ Pilih Penapis untuk Cetak</h3>
                            <button class="btn-close" id="closeReminderFilterModal">✖</button>
                        </div>
                        <div class="modal-body">
                            <div class="form-group">
                                <label for="filterZakatType">Jenis Zakat:</label>
                                <select id="filterZakatType" class="admin-select">
                                    <option value="">Semua Jenis Zakat</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="filterReminderYear">Tahun:</label>
                                <select id="filterReminderYear" class="admin-select">
                                    <option value="">Semua Tahun</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="filterReminderMonth">Bulan:</label>
                                <select id="filterReminderMonth" class="admin-select">
                                    <option value="">Semua Bulan</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="filterReminderAllTime">
                                    <span>Cetak semua rekod (abaikan tarikh)</span>
                                </label>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn ghost" id="cancelReminderFilter">Batal</button>
                            <button class="btn primary" id="confirmPrintReminderWithFilter">🖨️ Cetak</button>
                        </div>
                    </div>
                `;

                // Attach event listeners
                const closeBtn = modal.querySelector('#closeReminderFilterModal');
                const cancelBtn = modal.querySelector('#cancelReminderFilter');
                const confirmBtn = modal.querySelector('#confirmPrintReminderWithFilter');
                const overlay = modal.querySelector('.modal-overlay');
                const allTimeCheckbox = modal.querySelector('#filterReminderAllTime');
                const yearSelect = modal.querySelector('#filterReminderYear');
                const monthSelect = modal.querySelector('#filterReminderMonth');

                const closeModal = () => {
                    modal.style.display = 'none';
                };

                closeBtn.addEventListener('click', closeModal);
                cancelBtn.addEventListener('click', closeModal);
                overlay.addEventListener('click', closeModal);

                // Toggle date inputs based on "all time" checkbox
                allTimeCheckbox.addEventListener('change', (e) => {
                    yearSelect.disabled = e.target.checked;
                    monthSelect.disabled = e.target.checked;
                });

                confirmBtn.addEventListener('click', () => {
                    const zakatType = document.getElementById('filterZakatType').value;
                    const allTime = allTimeCheckbox.checked;
                    const year = yearSelect.value;
                    const month = monthSelect.value;

                    this.printWithFilter(zakatType, year, month, allTime);
                    closeModal();
                });

                return modal;
            },

            populateZakatTypeOptions() {
                const zakatTypeSelect = document.getElementById('filterZakatType');
                if (!zakatTypeSelect) return;

                const zakatTypes = [
                    { value: 'pendapatan', label: 'Pendapatan' },
                    { value: 'simpanan', label: 'Simpanan' },
                    { value: 'padi', label: 'Padi' },
                    { value: 'saham', label: 'Saham' },
                    { value: 'perak', label: 'Perak' },
                    { value: 'kwsp', label: 'KWSP' }
                ];

                zakatTypeSelect.innerHTML = '<option value="">Semua Jenis Zakat</option>' +
                    zakatTypes.map(type => `<option value="${type.value}">${type.label}</option>`).join('');
            },

            populateYearOptions() {
                const yearSelect = document.getElementById('filterReminderYear');
                if (!yearSelect) return;

                // Get unique years from reminders created_at dates
                const years = new Set();
                STATE.reminders.forEach(reminder => {
                    if (reminder.created_at) {
                        try {
                            // Parse date using Date object (handles GMT format)
                            const dateObj = new Date(reminder.created_at);
                            if (!isNaN(dateObj.getTime())) {
                                years.add(dateObj.getFullYear().toString());
                            }
                        } catch (e) {
                            // Fallback to regex
                            const dateStr = String(reminder.created_at);
                            const match = dateStr.match(/(\d{4})/);
                            if (match) {
                                years.add(match[1]);
                            }
                        }
                    }
                });

                const sortedYears = Array.from(years).sort((a, b) => b - a);

                // If no years found, add current year
                if (sortedYears.length === 0) {
                    sortedYears.push(new Date().getFullYear().toString());
                }

                yearSelect.innerHTML = '<option value="">Semua Tahun</option>' +
                    sortedYears.map(year => `<option value="${year}">${year}</option>`).join('');

                // Set current year as default
                const currentYear = new Date().getFullYear().toString();
                if (sortedYears.includes(currentYear)) {
                    yearSelect.value = currentYear;
                }
            },

            populateMonthOptions() {
                const monthSelect = document.getElementById('filterReminderMonth');
                if (!monthSelect) return;

                const months = [
                    'Januari', 'Februari', 'Mac', 'April', 'Mei', 'Jun',
                    'Julai', 'Ogos', 'September', 'Oktober', 'November', 'Disember'
                ];

                monthSelect.innerHTML = '<option value="">Semua Bulan</option>' +
                    months.map((month, idx) => 
                        `<option value="${(idx + 1).toString().padStart(2, '0')}">${month}</option>`
                    ).join('');
            },

            printWithFilter(zakatType, year, month, allTime) {
                console.log('=== PRINT WITH FILTER DEBUG ===');
                console.log('Total reminders in STATE:', STATE.reminders.length);
                console.log('Filtered reminders before print:', STATE.filteredReminders.length);
                console.log('Filters:', { zakatType, year, month, allTime });

                // Start with currently filtered reminders (respects search/filter)
                let filteredReminders = [...STATE.filteredReminders];
                
                console.log('Starting with filtered reminders:', filteredReminders.length);

                // Apply zakat type filter
                if (zakatType) {
                    console.log('Applying zakat type filter:', zakatType);
                    
                    const beforeCount = filteredReminders.length;
                    filteredReminders = filteredReminders.filter(reminder => {
                        const normalizeType = (type) => {
                            if (!type) return '';
                            const typeMap = {
                                'income_kaedah_a': 'pendapatan',
                                'income_kaedah_b': 'pendapatan',
                                'savings': 'simpanan'
                            };
                            return typeMap[type] || type;
                        };

                        const reminderType = normalizeType(reminder.zakat_type);
                        const matches = reminderType === zakatType;
                        
                        if (!matches) {
                            console.log('Filtered out:', reminder.name, 'type:', reminder.zakat_type, 'normalized:', reminderType);
                        }
                        
                        return matches;
                    });
                    
                    console.log('After zakat type filter:', beforeCount, '->', filteredReminders.length);
                }

                // Apply date filter only if not "all time"
                if (!allTime && (year || month)) {
                    console.log('Applying date filter. Year:', year, 'Month:', month);
                    
                    const beforeCount = filteredReminders.length;
                    filteredReminders = filteredReminders.filter(reminder => {
                        if (!reminder.created_at) {
                            console.log('No created_at for:', reminder.name);
                            return false;
                        }

                        const dateStr = String(reminder.created_at);
                        console.log('Processing date:', dateStr, 'for', reminder.name);

                        let logYear, logMonth, logDay;

                        // Try to parse as Date object first (handles GMT format)
                        try {
                            const dateObj = new Date(dateStr);
                            if (!isNaN(dateObj.getTime())) {
                                // Successfully parsed as Date
                                logYear = dateObj.getFullYear().toString();
                                logMonth = (dateObj.getMonth() + 1).toString().padStart(2, '0');
                                logDay = dateObj.getDate().toString().padStart(2, '0');
                                console.log('Parsed via Date object:', { logYear, logMonth, logDay });
                            } else {
                                throw new Error('Invalid date');
                            }
                        } catch (e) {
                            // Fallback to regex patterns
                            // Pattern 1: YYYY-MM-DD (ISO format)
                            let dateMatch = dateStr.match(/(\d{4})-(\d{2})-(\d{2})/);
                            
                            // Pattern 2: DD/MM/YYYY
                            if (!dateMatch) {
                                dateMatch = dateStr.match(/(\d{2})\/(\d{2})\/(\d{4})/);
                                if (dateMatch) {
                                    // Reorder to [year, month, day]
                                    dateMatch = [dateMatch[0], dateMatch[3], dateMatch[2], dateMatch[1]];
                                }
                            }

                            if (!dateMatch) {
                                console.log('Could not parse date:', dateStr);
                                return false;
                            }

                            [, logYear, logMonth, logDay] = dateMatch;
                            console.log('Parsed via regex:', { logYear, logMonth, logDay });
                        }

                        // Check year match - ONLY if year filter is provided
                        if (year && year.trim() !== '') {
                            if (logYear !== year) {
                                console.log('Year mismatch:', logYear, '!==', year);
                                return false;
                            }
                        }

                        // Check month match - ONLY if month filter is provided
                        if (month && month.trim() !== '') {
                            if (logMonth !== month) {
                                console.log('Month mismatch:', logMonth, '!==', month);
                                return false;
                            }
                        }

                        console.log('Date matches!');
                        return true;
                    });
                    
                    console.log('After date filter:', beforeCount, '->', filteredReminders.length);
                } else if (allTime) {
                    console.log('All time selected - skipping date filter');
                }

                console.log('Final filtered count:', filteredReminders.length);
                console.log('=== END DEBUG ===');

                // Show alert if no records
                if (filteredReminders.length === 0) {
                    alert('Tiada rekod ditemui untuk penapis yang dipilih.\n\nSila semak:\n- Adakah data wujud untuk penapis tersebut?\n- Cuba pilih "Cetak semua rekod"');
                    return;
                }

                // Proceed with printing
                this.printAll(filteredReminders, zakatType, year, month, allTime);
            },

            printAll(reminders = null, filterZakatType = null, filterYear = null, filterMonth = null, allTime = false) {
                const remindersToPrint = reminders || STATE.filteredReminders;

                if (remindersToPrint.length === 0) {
                    alert('Tiada reminder untuk dicetak');
                    return;
                }

                const printWindow = window.open('', '_blank');
                const content = this.generatePrintContent(remindersToPrint, filterZakatType, filterYear, filterMonth, allTime);

                printWindow.document.write(content);
                printWindow.document.close();
                printWindow.focus();

                setTimeout(() => {
                    printWindow.print();
                }, 500);
            },

            generatePrintContent(reminders, filterZakatType, filterYear, filterMonth, allTime) {
                const now = new Date().toLocaleString('ms-MY');
                const totalAmount = reminders.reduce((sum, r) => sum + (parseFloat(r.zakat_amount) || 0), 0);

                // Format filter info
                let filterInfo = [];
                
                if (filterZakatType) {
                    const zakatTypeNames = {
                        'pendapatan': 'Pendapatan',
                        'simpanan': 'Simpanan',
                        'padi': 'Padi',
                        'saham': 'Saham',
                        'perak': 'Perak',
                        'kwsp': 'KWSP'
                    };
                    filterInfo.push(`Jenis: ${zakatTypeNames[filterZakatType] || filterZakatType}`);
                }

                if (!allTime) {
                    const monthNames = [
                        'Januari', 'Februari', 'Mac', 'April', 'Mei', 'Jun',
                        'Julai', 'Ogos', 'September', 'Oktober', 'November', 'Disember'
                    ];
                    
                    if (filterYear && filterMonth) {
                        const monthName = monthNames[parseInt(filterMonth) - 1];
                        filterInfo.push(`Tempoh: ${monthName} ${filterYear}`);
                    } else if (filterYear) {
                        filterInfo.push(`Tempoh: Tahun ${filterYear}`);
                    } else if (filterMonth) {
                        const monthName = monthNames[parseInt(filterMonth) - 1];
                        filterInfo.push(`Tempoh: ${monthName}`);
                    }
                } else if (!filterZakatType) {
                    filterInfo.push('Semua Rekod');
                }

                const filterDisplay = filterInfo.length > 0 ? filterInfo.join(' | ') : 'Semua Rekod';

                return `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Reminder Report - LZNK</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 20px; }
                            .header { text-align: center; margin-bottom: 30px; border-bottom: 3px solid #006a4e; padding-bottom: 15px; }
                            .header h1 { color: #006a4e; margin: 0; }
                            .header p { color: #666; margin: 5px 0; }
                            .filter-info { 
                                background: #f0f9ff; 
                                padding: 12px; 
                                border-left: 4px solid #006a4e; 
                                margin-bottom: 20px;
                                font-weight: 600;
                            }
                            .stats { 
                                margin: 20px 0; 
                                padding: 15px; 
                                background: #f0f0f0; 
                                border-radius: 8px; 
                                display: grid;
                                grid-template-columns: repeat(2, 1fr);
                                gap: 15px;
                            }
                            .stat-box { text-align: center; }
                            .stat-label { font-size: 12px; color: #666; }
                            .stat-value { font-size: 24px; font-weight: bold; color: #006a4e; }
                            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                            th { background: #006a4e; color: white; padding: 10px; text-align: left; font-size: 12px; }
                            td { padding: 8px; border-bottom: 1px solid #ddd; font-size: 11px; }
                            tr:nth-child(even) { background: #f9f9f9; }
                            .footer { margin-top: 30px; text-align: center; color: #666; font-size: 12px; }
                            @media print {
                                body { margin: 0; }
                                .no-print { display: none; }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>🔔 Zakat Reminder Report</h1>
                            <p>Lembaga Zakat Negeri Kedah (LZNK)</p>
                            <p>Generated: ${now}</p>
                        </div>

                        <div class="filter-info">
                            📋 Penapis: ${filterDisplay}
                        </div>

                        <div class="stats">
                            <div class="stat-box">
                                <div class="stat-label">Total Reminders</div>
                                <div class="stat-value">${reminders.length}</div>
                            </div>
                            <div class="stat-box">
                                <div class="stat-label">Total Zakat Amount</div>
                                <div class="stat-value">RM ${totalAmount.toFixed(2)}</div>
                            </div>
                        </div>

                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>IC Number</th>
                                    <th>Phone</th>
                                    <th>Jenis Zakat</th>
                                    <th>Amount (RM)</th>
                                    <th>Tahun</th>
                                    <th>Tarikh Daftar</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${reminders.map(r => `
                                    <tr>
                                        <td>${r.id_reminder}</td>
                                        <td>${UIManager.escapeHtml(r.name)}</td>
                                        <td>${UIManager.formatIC(r.ic_number)}</td>
                                        <td>${UIManager.formatPhone(r.phone)}</td>
                                        <td>${UIManager.escapeHtml(UIManager.formatZakatType(r.zakat_type))}</td>
                                        <td>${UIManager.formatAmount(r.zakat_amount)}</td>
                                        <td>${UIManager.escapeHtml(UIManager.formatYear(r.year))}</td>
                                        <td>${UIManager.formatDate(r.created_at)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>

                        <div class="footer">
                            <p>© ${new Date().getFullYear()} Lembaga Zakat Negeri Kedah. All rights reserved.</p>
                            <p>This is a computer-generated report.</p>
                        </div>
                    </body>
                    </html>
                `;
            },

            printSingle(reminder) {
                const now = new Date().toLocaleString('ms-MY');

                const content = `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Reminder Details - ${reminder.name}</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 40px; }
                            .header { text-align: center; margin-bottom: 30px; border-bottom: 3px solid #006a4e; padding-bottom: 15px; }
                            .header h1 { color: #006a4e; margin: 0; }
                            .detail-card { border: 2px solid #006a4e; border-radius: 12px; padding: 30px; margin-top: 20px; }
                            .detail-row { display: flex; margin-bottom: 15px; padding: 10px; border-bottom: 1px solid #eee; }
                            .detail-label { font-weight: bold; width: 180px; color: #666; }
                            .detail-value { flex: 1; color: #333; }
                            .highlight { background: #f0f9f5; padding: 15px; margin: 20px 0; border-left: 4px solid #006a4e; }
                            .footer { margin-top: 40px; text-align: center; color: #666; font-size: 12px; }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>🔔 Zakat Reminder Details</h1>
                            <p>Lembaga Zakat Negeri Kedah (LZNK)</p>
                            <p>Generated: ${now}</p>
                        </div>

                        <div class="detail-card">
                            <h2>${UIManager.escapeHtml(reminder.name)}</h2>
                            
                            <div class="detail-row">
                                <span class="detail-label">Reminder ID:</span>
                                <span class="detail-value">#${reminder.id_reminder}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Full Name:</span>
                                <span class="detail-value">${UIManager.escapeHtml(reminder.name)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">IC Number:</span>
                                <span class="detail-value">${UIManager.formatIC(reminder.ic_number)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Phone Number:</span>
                                <span class="detail-value">${UIManager.formatPhone(reminder.phone)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Zakat Type:</span>
                                <span class="detail-value">${UIManager.escapeHtml(UIManager.formatZakatType(reminder.zakat_type))}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Tahun:</span>
                                <span class="detail-value">${UIManager.escapeHtml(UIManager.formatYear(reminder.year))}</span>
                            </div>
                            
                            <div class="highlight">
                                <div class="detail-row" style="border: none; margin: 0;">
                                    <span class="detail-label">Zakat Amount:</span>
                                    <span class="detail-value" style="font-size: 24px; font-weight: bold; color: #006a4e;">
                                        ${UIManager.formatAmount(reminder.zakat_amount)}
                                    </span>
                                </div>
                            </div>

                            <div class="detail-row">
                                <span class="detail-label">Registration Date:</span>
                                <span class="detail-value">${UIManager.formatDate(reminder.created_at)}</span>
                            </div>
                        </div>

                        <div class="footer">
                            <p>© ${new Date().getFullYear()} Lembaga Zakat Negeri Kedah. All rights reserved.</p>
                            <p>This is a computer-generated document.</p>
                        </div>
                    </body>
                    </html>
                `;

                const printWindow = window.open('', '_blank');
                printWindow.document.write(content);
                printWindow.document.close();
                printWindow.focus();

                setTimeout(() => {
                    printWindow.print();
                }, 500);
            }
        };
                // Event Handlers
        const EventHandlers = {
            init() {
                // Search and filters
                if (DOM.reminderSearch) {
                    DOM.reminderSearch.addEventListener('input', () => {
                        ReminderOperations.applyFilters();
                    });
                }

                if (DOM.zakatTypeFilter) {
                    DOM.zakatTypeFilter.addEventListener('change', () => {
                        ReminderOperations.applyFilters();
                    });
                }

                // Refresh
                if (DOM.refreshReminders) {
                    DOM.refreshReminders.addEventListener('click', () => {
                        ReminderOperations.load();
                    });
                }

                // Print and Export
                if (DOM.printRemindersBtn) {
                    DOM.printRemindersBtn.addEventListener('click', () => {
                        PrintManager.showFilterModal();  // Changed from printAll()
                    });
                }


                if (DOM.exportRemindersBtn) {
                    DOM.exportRemindersBtn.addEventListener('click', () => {
                        ReminderOperations.exportCSV();
                    });
                }

                // Table actions
                if (DOM.reminderTableBody) {
                    DOM.reminderTableBody.addEventListener('click', (e) => {
                        const btn = e.target.closest('button');
                        if (!btn || STATE.isLoading) return;

                        const id = parseInt(btn.getAttribute('data-id'));
                        const action = btn.getAttribute('data-action');
                        const reminder = STATE.reminders.find(r => r.id_reminder === id);

                        if (action === 'view' && reminder) {
                            ReminderOperations.viewDetails(id);
                        } else if (action === 'delete' && reminder) {
                            ReminderOperations.delete(id, reminder.name);
                        }
                    });
                }

                // Modal close
                const modal = document.getElementById('reminderDetailModal');
                if (modal) {
                    const overlay = modal.querySelector('.modal-overlay');
                    if (overlay) {
                        overlay.addEventListener('click', () => {
                            modal.style.display = 'none';
                        });
                    }
                }
            }
        };

        // Initialize
        EventHandlers.init();

        // Make functions available globally for inline handlers
        window.ReminderOperations = ReminderOperations;
    });
})();