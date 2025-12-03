// =========================
// ADMIN REMINDERS HANDLER
// =========================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const CONFIG = {
            API_BASE: 'http://127.0.0.1:5000/admin/reminders',
            STATS_API: 'http://127.0.0.1:5000/admin/reminders/stats',
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
            totalReminders: document.getElementById('totalReminders')
        };

        let STATE = {
            reminders: [],
            filteredReminders: [],
            currentPage: 1,
            totalPages: 1,
            isLoading: false,
            stats: null
        };

        // Navigation Handler (chatlog removed)
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.getAttribute('data-section');

                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');

                document.querySelectorAll('.content-section').forEach(sec => {
                    sec.style.display = 'none';
                });

                if (section === 'reminders') {
                    document.getElementById('remindersSection').style.display = 'block';
                    ReminderOperations.load();
                } else if (section === 'faqs') {
                    document.getElementById('faqSection').style.display = 'block';
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
                if (ic.length === 12) {
                    return `${ic.substr(0, 6)}-${ic.substr(6, 2)}-${ic.substr(8, 4)}`;
                }
                return ic;
            },

            formatPhone(phone) {
                if (!phone) return '';
                if (phone.length >= 10) {
                    return `${phone.substr(0, 3)}-${phone.substr(3, 3)} ${phone.substr(6)}`;
                }
                return phone;
            },

            formatZakatType(zakatType) {
                if (!zakatType) return 'N/A';
                return zakatType.charAt(0).toUpperCase() + zakatType.slice(1).toLowerCase();
            },

            formatYear(year) {
                if (!year) return 'N/A';
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
                                ${r.zakat_type === 'pendapatan' ? '💼' : '💰'} 
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

                DOM.reminderPagination.querySelectorAll('.page-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const page = parseInt(btn.getAttribute('data-page'));
                        ReminderOperations.changePage(page);
                    });
                });
            },

            updateStats(stats) {
                if (!stats) return;

                if (DOM.statsTotal) DOM.statsTotal.textContent = stats.total || 0;
                if (DOM.totalReminders) DOM.totalReminders.textContent = stats.total || 0;

                if (DOM.statsTotalAmount) {
                    DOM.statsTotalAmount.textContent = this.formatAmount(stats.total_amount);
                }

                const byType = stats.by_type || [];
                let pendapatanCount = 0;
                let simpananCount = 0;

                byType.forEach(item => {
                    if (item.zakat_type === 'pendapatan') pendapatanCount = item.count;
                    if (item.zakat_type === 'simpanan') simpananCount = item.count;
                });

                if (DOM.statsPendapatan) DOM.statsPendapatan.textContent = pendapatanCount;
                if (DOM.statsSimpanan) DOM.statsSimpanan.textContent = simpananCount;
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
                    if (!data.hasOwnProperty('stats')) {
                        console.warn('Unexpected stats response format:', data);
                        return { stats: null };
                    }

                    return data;

                } catch (error) {
                    console.error('Error fetching stats:', error);
                    return { stats: { total: 0, total_amount: 0, by_type: [] } };
                }
            },

            async deleteReminder(id) {
                const res = await fetch(`${CONFIG.API_BASE}/${id}`, { method: 'DELETE' });
                if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                return await res.json();
            },

            async getReminder(id) {
                const res = await fetch(`${CONFIG.API_BASE}/${id}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                return await res.json();
            }
        };

        const ReminderOperations = {
            async load() {
                try {
                    UIManager.showLoading(true);
                    UIManager.updateStatus('⏳ Memuat reminders...');

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
                    }

                    STATE.reminders = reminderData.reminders || [];
                    STATE.stats = statsData.stats || null;

                    this.applyFilters();
                    UIManager.updateStats(STATE.stats);

                    if (STATE.reminders.length > 0) {
                        UIManager.updateStatus(`✅ ${STATE.reminders.length} reminders loaded`);
                    } else {
                        UIManager.updateStatus('ℹ️ Tiada reminders ditemui');
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

                    const matchesType = !zakatType || r.zakat_type === zakatType;
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
                                ${reminder.zakat_type === 'pendapatan' ? '💼' : '💰'} 
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
                const printBtn = document.getElementById('printSingleReminder');
                printBtn.onclick = () => PrintManager.printSingle(reminder);
            },

            exportCSV() {
                if (STATE.filteredReminders.length === 0) {
                    alert('No reminders to export');
                    return;
                }

                const headers = [
                    'ID',
                    'Name',
                    'IC Number',
                    'Phone',
                    'Jenis Zakat',
                    'Zakat Amount',
                    'Tahun',
                    'Tarikh Daftar'
                ];

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

    });
})();
