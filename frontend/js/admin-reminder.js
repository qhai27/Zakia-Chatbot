// =========================
// ADMIN REMINDERS HANDLER
// =========================

(function() {
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
                    return `${ic.substr(0,6)}-${ic.substr(6,2)}-${ic.substr(8,4)}`;
                }
                return ic;
            },

            formatPhone(phone) {
                if (!phone) return '';
                // Format phone as 012-345 6789
                if (phone.length >= 10) {
                    return `${phone.substr(0,3)}-${phone.substr(3,3)} ${phone.substr(6)}`;
                }
                return phone;
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
                        <td><span class="id-badge">#${r.id}</span></td>
                        <td><strong>${this.escapeHtml(r.name)}</strong></td>
                        <td><code>${this.formatIC(r.ic_number)}</code></td>
                        <td><code>${this.formatPhone(r.phone)}</code></td>
                        <td>
                            <span class="zakat-type-badge ${r.zakat_type || 'umum'}">
                                ${r.zakat_type === 'pendapatan' ? '💼' : '💰'} 
                                ${this.escapeHtml(r.zakat_type || 'Umum')}
                            </span>
                        </td>
                        <td class="amount-cell">${this.formatAmount(r.zakat_amount)}</td>
                        <td class="date-cell">${this.formatDate(r.created_at)}</td>
                        <td>
                            <div class="admin-actions">
                                <button class="btn ghost btn-sm" data-action="view" data-id="${r.id}" title="View Details">
                                    👁️ View
                                </button>
                                <button class="btn warn btn-sm" data-action="delete" data-id="${r.id}" title="Delete">
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

                byType.forEach(item => {
                    if (item.zakat_type === 'pendapatan') {
                        pendapatanCount = item.count;
                    } else if (item.zakat_type === 'simpanan') {
                        simpananCount = item.count;
                    }
                });

                if (DOM.statsPendapatan) {
                    DOM.statsPendapatan.textContent = pendapatanCount;
                }
                if (DOM.statsSimpanan) {
                    DOM.statsSimpanan.textContent = simpananCount;
                }

                // Animate stats
                [DOM.statsTotal, DOM.statsTotalAmount, DOM.statsPendapatan, DOM.statsSimpanan].forEach(el => {
                    if (el) {
                        el.style.transform = 'scale(1.15)';
                        setTimeout(() => {
                            el.style.transform = 'scale(1)';
                        }, 200);
                    }
                });
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
                if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                return await res.json();
            },

            async fetchStats() {
                const res = await fetch(CONFIG.STATS_API);
                if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                return await res.json();
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
            }
        };

        const ReminderOperations = {
            async load() {
                try {
                    UIManager.showLoading(true);
                    UIManager.updateStatus('⏳ Memuat reminders...');

                    // Load reminders and stats
                    const [reminderData, statsData] = await Promise.all([
                        APIService.fetchReminders(),
                        APIService.fetchStats()
                    ]);

                    STATE.reminders = reminderData.reminders || [];
                    STATE.stats = statsData.stats || null;
                    
                    this.applyFilters();
                    UIManager.updateStats(STATE.stats);
                    UIManager.updateStatus(`✅ ${STATE.reminders.length} reminders loaded`);
                } catch (error) {
                    console.error('Error loading reminders:', error);
                    UIManager.updateStatus(`❌ Error: ${error.message}`, true);
                    STATE.reminders = [];
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
                                ${UIManager.escapeHtml(reminder.zakat_type || 'Umum')}
                            </span>
                        </div>
                        
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>ID:</label>
                                <span class="id-badge">#${reminder.id}</span>
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
                                <span>${UIManager.escapeHtml(reminder.zakat_type || 'N/A')}</span>
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

                const headers = ['ID', 'Name', 'IC Number', 'Phone', 'Zakat Type', 'Zakat Amount', 'Created Date'];
                const rows = STATE.filteredReminders.map(r => [
                    r.id,
                    r.name,
                    r.ic_number,
                    r.phone,
                    r.zakat_type || '',
                    r.zakat_amount || 0,
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

        const PrintManager = {
            printAll() {
                if (STATE.filteredReminders.length === 0) {
                    alert('No reminders to print');
                    return;
                }

                const printWindow = window.open('', '_blank');
                const content = this.generatePrintContent(STATE.filteredReminders, STATE.stats);
                
                printWindow.document.write(content);
                printWindow.document.close();
                printWindow.focus();
                
                setTimeout(() => {
                    printWindow.print();
                }, 500);
            },

            printSingle(reminder) {
                const printWindow = window.open('', '_blank');
                const content = this.generateSinglePrintContent(reminder);
                
                printWindow.document.write(content);
                printWindow.document.close();
                printWindow.focus();
                
                setTimeout(() => {
                    printWindow.print();
                }, 500);
            },

            generatePrintContent(reminders, stats) {
                const now = new Date().toLocaleString('ms-MY');
                const totalAmount = reminders.reduce((sum, r) => sum + (parseFloat(r.zakat_amount) || 0), 0);

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
                            .stats { margin: 20px 0; padding: 15px; background: #f0f0f0; border-radius: 8px; }
                            .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
                            .stat-box { text-align: center; }
                            .stat-label { font-size: 12px; color: #666; }
                            .stat-value { font-size: 24px; font-weight: bold; color: #006a4e; }
                            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                            th { background: #006a4e; color: white; padding: 10px; text-align: left; }
                            td { padding: 8px; border-bottom: 1px solid #ddd; }
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

                        <div class="stats">
                            <div class="stats-grid">
                                <div class="stat-box">
                                    <div class="stat-label">Total Reminders</div>
                                    <div class="stat-value">${reminders.length}</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-label">Total Zakat Amount</div>
                                    <div class="stat-value">RM ${totalAmount.toFixed(2)}</div>
                                </div>
                                <div class="stat-box">
                                    <div class="stat-label">Report Date</div>
                                    <div class="stat-value">${new Date().toLocaleDateString('ms-MY')}</div>
                                </div>
                            </div>
                        </div>

                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>IC Number</th>
                                    <th>Phone</th>
                                    <th>Zakat Type</th>
                                    <th>Amount (RM)</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${reminders.map(r => `
                                    <tr>
                                        <td>${r.id}</td>
                                        <td>${UIManager.escapeHtml(r.name)}</td>
                                        <td>${UIManager.formatIC(r.ic_number)}</td>
                                        <td>${UIManager.formatPhone(r.phone)}</td>
                                        <td>${UIManager.escapeHtml(r.zakat_type || 'N/A')}</td>
                                        <td>${UIManager.formatAmount(r.zakat_amount)}</td>
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

            generateSinglePrintContent(reminder) {
                const now = new Date().toLocaleString('ms-MY');

                return `
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
                                <span class="detail-value">#${reminder.id}</span>
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
                                <span class="detail-value">${UIManager.escapeHtml(reminder.zakat_type || 'N/A')}</span>
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
                        PrintManager.printAll();
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
                        const reminder = STATE.reminders.find(r => r.id === id);

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