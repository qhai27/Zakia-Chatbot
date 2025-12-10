// =========================
// ADMIN CHAT LOG HANDLER 
// =========================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const CONFIG = {
            API_BASE: 'http://127.0.0.1:5000/admin/chat-logs',
            PAGE_SIZE: 50,
            AUTO_REFRESH_INTERVAL: 10000,
            FORCE_NO_CACHE: true 
        };

        const DOM = {
            chatlogTableBody: document.getElementById('chatlogTableBody'),
            chatlogEmptyState: document.getElementById('chatlogEmptyState'),
            chatlogStatus: document.getElementById('chatlogStatus'),
            refreshChatLogs: document.getElementById('refreshChatLogs'),
            chatlogSearch: document.getElementById('chatlogSearch'),
            chatlogPagination: document.getElementById('chatlogPagination'),
            exportChatLogsBtn: document.getElementById('exportChatLogsBtn'),
            printChatLogsBtn: document.getElementById('printChatLogsBtn'),
            statsTotal: document.getElementById('statsChatTotal'),
            totalChatLogs: document.getElementById('totalChatLogs'),
            selectAllCheckbox: document.getElementById('selectAllCheckbox'),
            bulkDeleteBtn: document.getElementById('bulkDeleteBtn')
        };

        let STATE = {
        logs: [],
        filteredLogs: [],
        currentPage: 1,
        totalPages: 1,
        isLoading: false,
        selectedLogs: new Set(),
        autoRefreshTimer: null,
        lastFetchTime: null, // NEW
        isSectionActive: false // NEW
        };

        const UIManager = {
            updateStatus(message, isError = false) {
                if (DOM.chatlogStatus) {
                    DOM.chatlogStatus.textContent = message;
                    DOM.chatlogStatus.style.color = isError ? '#e53935' : '#718096';
                }
            },

            showLoading(show = true) {
                STATE.isLoading = show;
                if (DOM.refreshChatLogs) {
                    DOM.refreshChatLogs.disabled = show;
                    DOM.refreshChatLogs.innerHTML = show ? '⏳ Memuat...' : '🔄 Refresh';
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
                
                try {
                    const parts = dateStr.match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);
                    if (parts) {
                        const [, year, month, day, hour, min, sec] = parts;
                        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                        const monthName = monthNames[parseInt(month) - 1];
                        return `${day} ${monthName} ${year}, ${hour}:${min}:${sec}`;
                    }
                    return dateStr;
                } catch (e) {
                    console.error('Date formatting error:', e);
                    return dateStr || 'N/A';
                }
            },

            truncateText(text, maxLength = 80) {
                if (!text) return '';
                return text.length > maxLength 
                    ? text.substring(0, maxLength) + '...' 
                    : text;
            },

            highlightSearchTerm(text, searchTerm) {
                if (!searchTerm || !text) return this.escapeHtml(text);
                const escaped = this.escapeHtml(text);
                const regex = new RegExp(`(${searchTerm})`, 'gi');
                return escaped.replace(regex, '<mark>$1</mark>');
            },

            renderLogs(logs) {
                if (!DOM.chatlogTableBody) return;

                if (logs.length === 0) {
                    DOM.chatlogTableBody.innerHTML = '';
                    if (DOM.chatlogEmptyState) DOM.chatlogEmptyState.style.display = 'block';
                    return;
                }

                if (DOM.chatlogEmptyState) DOM.chatlogEmptyState.style.display = 'none';

                const searchTerm = (DOM.chatlogSearch?.value || '').trim();

                DOM.chatlogTableBody.innerHTML = logs.map(log => {
                    const isSelected = STATE.selectedLogs.has(log.id_log);
                    return `
                    <tr class="${isSelected ? 'row-selected' : ''}" data-log-id="${log.id_log}">
                        <td>
                            <input type="checkbox" class="log-checkbox" data-id="${log.id_log}" 
                                ${isSelected ? 'checked' : ''} 
                                aria-label="Select log ${log.id_log}">
                        </td>
                        <td><span class="id-badge">#${log.id_log}</span></td>
                        <td>${log.id_user != null ? `<span class="user-id-badge">#${log.id_user}</span>` : '<span class="text-muted">-</span>'}</td>
                        <td><code class="session-code">${this.escapeHtml((log.session_id || '').substring(0, 8))}...</code></td>
                        <td class="message-cell">
                            <div class="message-preview user-message-preview">
                                ${searchTerm ? this.highlightSearchTerm(this.truncateText(log.user_message, 60), searchTerm) : this.escapeHtml(this.truncateText(log.user_message, 60))}
                            </div>
                        </td>
                        <td class="message-cell">
                            <div class="message-preview bot-message-preview">
                                ${searchTerm ? this.highlightSearchTerm(this.truncateText(log.bot_response, 60), searchTerm) : this.escapeHtml(this.truncateText(log.bot_response, 60))}
                            </div>
                        </td>
                        <td class="date-cell">${this.formatDate(log.created_at)}</td>
                        <td>
                            <div class="admin-actions">
                                <button class="btn ghost btn-sm" data-action="view" data-id="${log.id_log}" title="Papar Butiran">
                                    👁️ Papar
                                </button>
                                <button class="btn warn btn-sm" data-action="delete" data-id="${log.id_log}" title="Padam">
                                    🗑️
                                </button>
                            </div>
                        </td>
                    </tr>
                `}).join('');

                this.attachCheckboxListeners();
            },

            attachCheckboxListeners() {
                const checkboxes = document.querySelectorAll('.log-checkbox');
                checkboxes.forEach(cb => {
                    cb.addEventListener('change', (e) => {
                        const id = parseInt(e.target.getAttribute('data-id'));
                        const row = e.target.closest('tr');
                        
                        if (e.target.checked) {
                            STATE.selectedLogs.add(id);
                            row.classList.add('row-selected');
                        } else {
                            STATE.selectedLogs.delete(id);
                            row.classList.remove('row-selected');
                        }
                        
                        this.updateBulkActions();
                    });
                });
            },

            updateBulkActions() {
                if (DOM.bulkDeleteBtn) {
                    DOM.bulkDeleteBtn.disabled = STATE.selectedLogs.size === 0;
                    DOM.bulkDeleteBtn.innerHTML = `🗑️ Padam (${STATE.selectedLogs.size})`;
                }
                
                if (DOM.selectAllCheckbox) {
                    const visibleLogs = STATE.filteredLogs.slice(
                        (STATE.currentPage - 1) * CONFIG.PAGE_SIZE,
                        STATE.currentPage * CONFIG.PAGE_SIZE
                    );
                    const allSelected = visibleLogs.length > 0 && 
                        visibleLogs.every(log => STATE.selectedLogs.has(log.id_log));
                    DOM.selectAllCheckbox.checked = allSelected;
                }
            },

            renderPagination(currentPage, totalPages) {
                if (!DOM.chatlogPagination || totalPages <= 1) {
                    if (DOM.chatlogPagination) DOM.chatlogPagination.innerHTML = '';
                    return;
                }

                const pages = [];
                const maxVisible = 5;
                let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
                let endPage = Math.min(totalPages, startPage + maxVisible - 1);

                if (endPage - startPage < maxVisible - 1) {
                    startPage = Math.max(1, endPage - maxVisible + 1);
                }

                if (startPage > 1) {
                    pages.push(`<button class="page-btn" data-page="1">« First</button>`);
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

                if (endPage < totalPages) {
                    pages.push(`<button class="page-btn" data-page="${totalPages}">Last »</button>`);
                }

                const startIdx = (currentPage - 1) * CONFIG.PAGE_SIZE + 1;
                const endIdx = Math.min(currentPage * CONFIG.PAGE_SIZE, STATE.filteredLogs.length);

                DOM.chatlogPagination.innerHTML = `
                    <div class="pagination-info">
                        <span class="pagination-text">
                            Showing ${startIdx}-${endIdx} of ${STATE.filteredLogs.length} logs
                            ${STATE.filteredLogs.length !== STATE.logs.length ? ` (filtered from ${STATE.logs.length} total)` : ''}
                        </span>
                    </div>
                    <div class="pagination-buttons">
                        ${pages.join('')}
                    </div>
                `;

                DOM.chatlogPagination.querySelectorAll('.page-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const page = parseInt(btn.getAttribute('data-page'));
                        ChatLogOperations.changePage(page);
                    });
                });
            },

            updateStats() {
                if (DOM.statsTotal) {
                    DOM.statsTotal.textContent = STATE.logs.length;
                }
                if (DOM.totalChatLogs) {
                    DOM.totalChatLogs.textContent = STATE.logs.length;
                }
            }
        };

        const APIService = {
            async fetchChatLogs(limit = 10000, offset = 0) {
                // Add timestamp to URL to prevent caching
                const timestamp = Date.now();
                const params = new URLSearchParams({
                    limit: limit.toString(),
                    offset: offset.toString(),
                    _t: timestamp.toString()
                });

                console.log(`[API] Fetching chat logs: ${CONFIG.API_BASE}?${params}`);

                // Simple fetch without cache-control headers
                const res = await fetch(`${CONFIG.API_BASE}?${params}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    const errorMsg = errorData.error || `HTTP ${res.status}: ${res.statusText}`;
                    throw new Error(errorMsg);
                }

                const data = await res.json();

                if (!data.hasOwnProperty('logs')) {
                    console.warn('Unexpected response format:', data);
                    return { logs: [], count: 0, total: 0 };
                }

                console.log(`[API] Received ${data.logs.length} logs (total: ${data.total})`);
                return data;
            },
            async getChatLog(id) {
                const res = await fetch(`${CONFIG.API_BASE}/${id}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                return await res.json();
            },

            async deleteChatLog(id) {
                const res = await fetch(`${CONFIG.API_BASE}/${id}`, { 
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' }
                });
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
                }
                return await res.json();
            },

            async bulkDeleteChatLogs(ids) {
                const res = await fetch(`${CONFIG.API_BASE}/bulk-delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids })
                });
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
                }
                return await res.json();
            }
        };

        const ChatLogOperations = {
            async load(silent = false) {
                try {
                    if (!silent) {
                        UIManager.showLoading(true);
                        UIManager.updateStatus('⏳ Memuat chat logs...');
                    }

                    const previousCount = STATE.logs.length;
                    const data = await APIService.fetchChatLogs();
                    const newLogs = data.logs || [];
                    
                    // NEW: Detect new entries
                    const newCount = newLogs.length - previousCount;
                    
                    STATE.logs = newLogs;
                    STATE.lastFetchTime = new Date(); // NEW
                    
                    // Clear selected logs that no longer exist
                    const existingIds = new Set(STATE.logs.map(l => l.id_log));
                    STATE.selectedLogs = new Set([...STATE.selectedLogs].filter(id => existingIds.has(id)));

                    this.applyFilters();
                    UIManager.updateStats();

                    if (STATE.logs.length > 0) {
                        const statusMsg = `✅ ${STATE.logs.length} chat logs loaded`;
                        UIManager.updateStatus(statusMsg);
                        
                        // NEW: Show indicator for new data
                        if (silent && newCount > 0) {
                            console.log(`[AUTO-REFRESH] Found ${newCount} new logs`);
                        }
                    } else {
                        UIManager.updateStatus('ℹ️ Tiada chat logs ditemui', false);
                    }
                } catch (error) {
                    console.error('[ERROR] Loading chat logs:', error);
                    UIManager.updateStatus(`❌ Error: ${error.message}`, true);
                    STATE.logs = [];
                    this.applyFilters();
                } finally {
                    if (!silent) {
                        UIManager.showLoading(false);
                    }
                }
            },

            applyFilters() {
                const search = (DOM.chatlogSearch?.value || '').toLowerCase().trim();

                STATE.filteredLogs = STATE.logs.filter(log => {
                    if (!search) return true;

                    const searchableText = [
                        log.user_message,
                        log.bot_response,
                        log.session_id,
                        log.id_user?.toString(),
                        log.id_log?.toString()
                    ].filter(Boolean).join(' ').toLowerCase();

                    return searchableText.includes(search);
                });

                STATE.totalPages = Math.ceil(STATE.filteredLogs.length / CONFIG.PAGE_SIZE);
                STATE.currentPage = 1;
                this.renderCurrentPage();
            },

            renderCurrentPage() {
                const startIdx = (STATE.currentPage - 1) * CONFIG.PAGE_SIZE;
                const endIdx = startIdx + CONFIG.PAGE_SIZE;
                const pageLogs = STATE.filteredLogs.slice(startIdx, endIdx);

                UIManager.renderLogs(pageLogs);
                UIManager.renderPagination(STATE.currentPage, STATE.totalPages);
                UIManager.updateBulkActions();
            },

            changePage(page) {
                if (page < 1 || page > STATE.totalPages) return;
                STATE.currentPage = page;
                this.renderCurrentPage();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            },

            async viewDetails(id) {
                const log = STATE.logs.find(l => l.id_log === id);
                if (!log) {
                    alert('Chat log not found');
                    return;
                }

                this.showDetailModal(log);
            },

            showDetailModal(log) {
                const modal = document.getElementById('chatlogDetailModal') || this.createModal();
                const body = modal.querySelector('.modal-body');

                body.innerHTML = `
                    <div class="chatlog-detail-card">
                        <div class="detail-header">
                            <h2>💬 Chat Log Details</h2>
                            <span class="id-badge">#${log.id_log}</span>
                        </div>
                        
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>Log ID:</label>
                                <span class="id-badge">#${log.id_log}</span>
                            </div>
                            <div class="detail-item">
                                <label>User ID:</label>
                                <span>${log.id_user != null ? `<span class="user-id-badge">#${log.id_user}</span>` : '<span class="text-muted">N/A</span>'}</span>
                            </div>
                            <div class="detail-item full-width">
                                <label>Session ID:</label>
                                <code class="session-code-full">${UIManager.escapeHtml(log.session_id || 'N/A')}</code>
                            </div>
                            <div class="detail-item full-width">
                                <label>Timestamp:</label>
                                <span>${UIManager.formatDate(log.created_at)}</span>
                            </div>
                            <div class="detail-item full-width">
                                <label>User Message:</label>
                                <div class="message-box user-message">
                                    ${UIManager.escapeHtml(log.user_message || '')}
                                </div>
                            </div>
                            <div class="detail-item full-width">
                                <label>Bot Response:</label>
                                <div class="message-box bot-message">
                                    ${UIManager.escapeHtml(log.bot_response || '')}
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                modal.style.display = 'flex';
            },

            createModal() {
                const modal = document.createElement('div');
                modal.id = 'chatlogDetailModal';
                modal.className = 'modal';
                modal.innerHTML = `
                    <div class="modal-overlay"></div>
                    <div class="modal-content modal-large">
                        <div class="modal-header">
                            <h3>💬 Chat Log Details</h3>
                            <button class="btn-close">✖</button>
                        </div>
                        <div class="modal-body"></div>
                        <div class="modal-footer">
                            <button class="btn ghost close-modal">Tutup</button>
                        </div>
                    </div>
                `;

                document.body.appendChild(modal);

                const closeButtons = modal.querySelectorAll('.btn-close, .close-modal, .modal-overlay');
                closeButtons.forEach(btn => {
                    btn.addEventListener('click', () => {
                        modal.style.display = 'none';
                    });
                });

                return modal;
            },

            async delete(id) {
                const log = STATE.logs.find(l => l.id_log === id);
                if (!log) {
                    console.error('Log not found in STATE:', id);
                    alert('Chat log tidak ditemui');
                    return;
                }

                const confirmed = confirm(
                    `⚠️ Padam chat log #${id}?\n\nUser: ${log.user_message?.substring(0, 50)}...\n\nTindakan ini tidak boleh dibatalkan.`
                );
                if (!confirmed) return;

                console.log('Deleting chat log:', id);
                
                try {
                    UIManager.showLoading(true);
                    UIManager.updateStatus(`⏳ Memadam chat log #${id}...`);
                    
                    const result = await APIService.deleteChatLog(id);
                    
                    console.log('Delete result:', result);

                    if (result && result.success && result.deleted) {
                        console.log('✅ Delete successful, reloading data');
                        await this.load();
                        UIManager.updateStatus(`✅ Chat log #${id} berjaya dipadam`);
                    } else {
                        console.error('Delete failed - invalid response:', result);
                        throw new Error(result?.error || 'Delete operation failed');
                    }
                } catch (error) {
                    console.error('❌ Delete error:', error);
                    
                    // NEW: Check if error is 404 (record already deleted)
                    if (error.message.includes('404') || error.message.includes('not found')) {
                        console.log('⚠️ Record already deleted or does not exist, refreshing data...');
                        UIManager.updateStatus(`⚠️ Rekod sudah dipadam sebelum ini. Menyegarkan data...`);
                        
                        // Force reload to sync with server
                        await this.load();
                    } else {
                        UIManager.updateStatus(`❌ Gagal memadam: ${error.message}`, true);
                        alert(`Gagal memadam chat log:\n${error.message}`);
                        await this.load();
                    }
                } finally {
                    UIManager.showLoading(false);
                }
            },


            async bulkDelete() {
                if (STATE.selectedLogs.size === 0) return;

                const confirmed = confirm(
                    `⚠️ Padam ${STATE.selectedLogs.size} chat logs?`
                );
                if (!confirmed) return;

                try {
                    UIManager.showLoading(true);

                    const ids = Array.from(STATE.selectedLogs);
                    const result = await APIService.bulkDeleteChatLogs(ids);

                    if (result.success) {

                        // Remove from local state
                        STATE.logs = STATE.logs.filter(l => !ids.includes(l.id_log));
                        STATE.selectedLogs.clear();

                        // Refilter without resetting page
                        this.applyFilters();

                        UIManager.updateStats();
                        UIManager.updateStatus(`✅ ${result.deleted_count} chat logs dipadam`);
                    } else {
                        throw new Error("Bulk delete failed");
                    }
                } catch (e) {
                    UIManager.updateStatus(`❌ Gagal: ${e.message}`, true);
                    await this.load();
                } finally {
                    UIManager.showLoading(false);
                }
            },


            toggleSelectAll() {
                const selectAllCheckbox = DOM.selectAllCheckbox;
                const visibleLogs = STATE.filteredLogs.slice(
                    (STATE.currentPage - 1) * CONFIG.PAGE_SIZE,
                    STATE.currentPage * CONFIG.PAGE_SIZE
                );

                if (selectAllCheckbox.checked) {
                    visibleLogs.forEach(log => STATE.selectedLogs.add(log.id_log));
                } else {
                    visibleLogs.forEach(log => STATE.selectedLogs.delete(log.id_log));
                }

                this.renderCurrentPage();
            },

            exportCSV() {
                if (STATE.filteredLogs.length === 0) {
                    alert('No chat logs to export');
                    return;
                }

                const headers = ['Log ID', 'User ID', 'Session ID', 'User Message', 'Bot Response', 'Timestamp'];
                const rows = STATE.filteredLogs.map(log => [
                    log.id_log,
                    log.id_user || '',
                    log.session_id || '',
                    log.user_message || '',
                    log.bot_response || '',
                    log.created_at || ''
                ]);

                const csvContent = [
                    headers.join(','),
                    ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
                ].join('\n');

                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);

                link.setAttribute('href', url);
                link.setAttribute('download', `chat_logs_${new Date().toISOString().split('T')[0]}.csv`);
                link.style.visibility = 'hidden';

                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            },

           startAutoRefresh() {
                console.log('[AUTO-REFRESH] Starting auto-refresh');
                
                // Clear any existing timer
                this.stopAutoRefresh();
                
                STATE.isSectionActive = true; // NEW

                // Set up new interval
                STATE.autoRefreshTimer = setInterval(() => {
                    if (STATE.isSectionActive && !STATE.isLoading) { // CHANGED: Check if active
                        console.log('[AUTO-REFRESH] Refreshing data...');
                        this.load(true); // Silent refresh
                    }
                }, CONFIG.AUTO_REFRESH_INTERVAL);
                
                console.log(`[AUTO-REFRESH] Timer set to ${CONFIG.AUTO_REFRESH_INTERVAL}ms`);
            },

            stopAutoRefresh() {
                if (STATE.autoRefreshTimer) {
                    console.log('[AUTO-REFRESH] Stopping auto-refresh');
                    clearInterval(STATE.autoRefreshTimer);
                    STATE.autoRefreshTimer = null;
                }
                STATE.isSectionActive = false; // NEW
            }
        };

        const DateFilterModal = {
            show() {
                // Create modal if doesn't exist
                let modal = document.getElementById('printDateFilterModal');
                if (!modal) {
                    modal = this.createModal();
                    document.body.appendChild(modal);
                }

                // Populate year and month options
                this.populateYearOptions();
                this.populateMonthOptions();

                modal.style.display = 'flex';
            },

            createModal() {
                const modal = document.createElement('div');
                modal.id = 'printDateFilterModal';
                modal.className = 'modal';
                modal.innerHTML = `
                    <div class="modal-overlay"></div>
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>🖨️ Pilih Tarikh untuk Cetak</h3>
                            <button class="btn-close" id="closeDateFilterModal">✖</button>
                        </div>
                        <div class="modal-body">
                            <div class="form-group">
                                <label for="filterYear">Tahun:</label>
                                <select id="filterYear" class="admin-select"></select>
                            </div>
                            <div class="form-group">
                                <label for="filterMonth">Bulan:</label>
                                <select id="filterMonth" class="admin-select">
                                    <option value="">Semua Bulan</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="filterAllTime">
                                    <span>Cetak semua rekod (abaikan tarikh)</span>
                                </label>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button class="btn ghost" id="cancelDateFilter">Batal</button>
                            <button class="btn primary" id="confirmPrintWithFilter">🖨️ Cetak</button>
                        </div>
                    </div>
                `;

                // Attach event listeners
                const closeBtn = modal.querySelector('#closeDateFilterModal');
                const cancelBtn = modal.querySelector('#cancelDateFilter');
                const confirmBtn = modal.querySelector('#confirmPrintWithFilter');
                const overlay = modal.querySelector('.modal-overlay');
                const allTimeCheckbox = modal.querySelector('#filterAllTime');
                const yearSelect = modal.querySelector('#filterYear');
                const monthSelect = modal.querySelector('#filterMonth');

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
                    const allTime = allTimeCheckbox.checked;
                    const year = yearSelect.value;
                    const month = monthSelect.value;

                    if (!allTime && !year) {
                        alert('Sila pilih tahun atau pilih "Cetak semua rekod"');
                        return;
                    }

                    PrintManager.printWithFilter(year, month, allTime);
                    closeModal();
                });

                return modal;
            },

            populateYearOptions() {
                const yearSelect = document.getElementById('filterYear');
                if (!yearSelect) return;

                // Get unique years from logs
                const years = new Set();
                STATE.logs.forEach(log => {
                    if (log.created_at) {
                        const match = log.created_at.match(/(\d{4})/);
                        if (match) {
                            years.add(match[1]);
                        }
                    }
                });

                const sortedYears = Array.from(years).sort((a, b) => b - a);

                yearSelect.innerHTML = '<option value="">Pilih Tahun</option>' +
                    sortedYears.map(year => `<option value="${year}">${year}</option>`).join('');

                // Set current year as default
                const currentYear = new Date().getFullYear().toString();
                if (sortedYears.includes(currentYear)) {
                    yearSelect.value = currentYear;
                }
            },

            populateMonthOptions() {
                const monthSelect = document.getElementById('filterMonth');
                if (!monthSelect) return;

                const months = [
                    'Januari', 'Februari', 'Mac', 'April', 'Mei', 'Jun',
                    'Julai', 'Ogos', 'September', 'Oktober', 'November', 'Disember'
                ];

                monthSelect.innerHTML = '<option value="">Semua Bulan</option>' +
                    months.map((month, idx) => 
                        `<option value="${(idx + 1).toString().padStart(2, '0')}">${month}</option>`
                    ).join('');
            }
        };

        const PrintManager = {
            printWithFilter(year, month, allTime) {
                let filteredLogs = STATE.filteredLogs;

                if (!allTime) {
                    filteredLogs = STATE.filteredLogs.filter(log => {
                        if (!log.created_at) return false;

                        const dateMatch = log.created_at.match(/(\d{4})-(\d{2})-(\d{2})/);
                        if (!dateMatch) return false;

                        const [, logYear, logMonth] = dateMatch;

                        if (year && logYear !== year) return false;
                        if (month && logMonth !== month) return false;

                        return true;
                    });
                }

                if (filteredLogs.length === 0) {
                    alert('Tiada rekod ditemui untuk tarikh yang dipilih');
                    return;
                }

                this.printAll(filteredLogs, year, month, allTime);
            },

            printAll(logs = null, filterYear = null, filterMonth = null, allTime = false) {
                const logsToPrint = logs || STATE.filteredLogs;

                if (logsToPrint.length === 0) {
                    alert('No chat logs to print');
                    return;
                }

                const printWindow = window.open('', '_blank');
                const content = this.generatePrintContent(logsToPrint, filterYear, filterMonth, allTime);

                printWindow.document.write(content);
                printWindow.document.close();
                printWindow.focus();

                setTimeout(() => {
                    printWindow.print();
                }, 500);
            },

            generatePrintContent(logs, filterYear, filterMonth, allTime) {
                const now = new Date().toLocaleString('ms-MY');
                
                // Format filter info
                let filterInfo = '';
                if (!allTime) {
                    const monthNames = [
                        'Januari', 'Februari', 'Mac', 'April', 'Mei', 'Jun',
                        'Julai', 'Ogos', 'September', 'Oktober', 'November', 'Disember'
                    ];
                    
                    if (filterYear && filterMonth) {
                        const monthName = monthNames[parseInt(filterMonth) - 1];
                        filterInfo = `${monthName} ${filterYear}`;
                    } else if (filterYear) {
                        filterInfo = `Tahun ${filterYear}`;
                    }
                } else {
                    filterInfo = 'Semua Rekod';
                }

                return `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Chat Log Report - LZNK</title>
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
                            .log-item { 
                                margin: 20px 0; 
                                padding: 15px; 
                                border: 1px solid #ddd; 
                                border-radius: 8px; 
                                page-break-inside: avoid; 
                            }
                            .log-header { 
                                display: flex; 
                                justify-content: space-between; 
                                margin-bottom: 10px; 
                                padding-bottom: 10px; 
                                border-bottom: 1px solid #eee; 
                            }
                            .log-id { font-weight: bold; color: #006a4e; }
                            .log-date { color: #666; font-size: 12px; }
                            .message-section { margin: 10px 0; }
                            .message-label { font-weight: bold; color: #333; margin-bottom: 5px; }
                            .user-message { 
                                background: #f0f9ff; 
                                padding: 10px; 
                                border-radius: 6px; 
                                margin-bottom: 10px; 
                            }
                            .bot-message { 
                                background: #f0fdf4; 
                                padding: 10px; 
                                border-radius: 6px; 
                            }
                            .footer { 
                                margin-top: 30px; 
                                text-align: center; 
                                color: #666; 
                                font-size: 12px; 
                            }
                            @media print {
                                body { margin: 0; }
                                .no-print { display: none; }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <h1>💬 Chat Log Report</h1>
                            <p>Lembaga Zakat Negeri Kedah (LZNK)</p>
                            <p>Generated: ${now}</p>
                            <p>Total Logs: ${logs.length}</p>
                        </div>

                        <div class="filter-info">
                            📅 Tempoh: ${filterInfo}
                        </div>

                        ${logs.map(log => `
                            <div class="log-item">
                                <div class="log-header">
                                    <span class="log-id">Log #${log.id_log} | User: ${log.id_user || 'N/A'}</span>
                                    <span class="log-date">${UIManager.formatDate(log.created_at)}</span>
                                </div>
                                <div class="message-section">
                                    <div class="message-label">User Message:</div>
                                    <div class="user-message">${UIManager.escapeHtml(log.user_message || '')}</div>
                                </div>
                                <div class="message-section">
                                    <div class="message-label">Bot Response:</div>
                                    <div class="bot-message">${UIManager.escapeHtml(log.bot_response || '')}</div>
                                </div>
                            </div>
                        `).join('')}

                        <div class="footer">
                            <p>© ${new Date().getFullYear()} Lembaga Zakat Negeri Kedah. All rights reserved.</p>
                            <p>This is a computer-generated report.</p>
                        </div>
                    </body>
                    </html>
                `;
            }
        };

        const EventHandlers = {
            init() {
                // Search
                if (DOM.chatlogSearch) {
                    let searchTimeout;
                    DOM.chatlogSearch.addEventListener('input', () => {
                        clearTimeout(searchTimeout);
                        searchTimeout = setTimeout(() => {
                            ChatLogOperations.applyFilters();
                        }, 300);
                    });
                }

                // Refresh
                if (DOM.refreshChatLogs) {
                    DOM.refreshChatLogs.addEventListener('click', () => {
                        ChatLogOperations.load();
                    });
                }

                // Export
                if (DOM.exportChatLogsBtn) {
                    DOM.exportChatLogsBtn.addEventListener('click', () => {
                        ChatLogOperations.exportCSV();
                    });
                }

                // Print - now shows date filter modal
                if (DOM.printChatLogsBtn) {
                    DOM.printChatLogsBtn.addEventListener('click', () => {
                        DateFilterModal.show();
                    });
                }

                // Select All
                if (DOM.selectAllCheckbox) {
                    DOM.selectAllCheckbox.addEventListener('change', () => {
                        ChatLogOperations.toggleSelectAll();
                    });
                }

                // Bulk Delete
                if (DOM.bulkDeleteBtn) {
                    DOM.bulkDeleteBtn.addEventListener('click', () => {
                        ChatLogOperations.bulkDelete();
                    });
                }

                // Table actions
                if (DOM.chatlogTableBody) {
                    DOM.chatlogTableBody.addEventListener('click', (e) => {
                        const btn = e.target.closest('button');
                        if (!btn || STATE.isLoading) return;

                        const id = parseInt(btn.getAttribute('data-id'));
                        const action = btn.getAttribute('data-action');

                        if (action === 'view') {
                            ChatLogOperations.viewDetails(id);
                        } else if (action === 'delete') {
                            ChatLogOperations.delete(id);
                        }
                    });
                }

                // Navigation handler
                const navItems = document.querySelectorAll('.nav-item');
                navItems.forEach(item => {
                    item.addEventListener('click', (e) => {
                        const section = item.getAttribute('data-section');
                        
                        if (section === 'chatlog') {
                            setTimeout(() => {
                                ChatLogOperations.load();
                                ChatLogOperations.startAutoRefresh();
                            }, 100);
                        } else {
                            ChatLogOperations.stopAutoRefresh();
                        }
                    });
                });

                // Stop auto-refresh when page is hidden
                // Force reload when page becomes visible (prevent stale data)
                document.addEventListener('visibilitychange', () => {
                    if (!document.hidden) {
                        const chatlogSection = document.getElementById('chatlogSection');
                        if (chatlogSection && chatlogSection.style.display !== 'none') {
                            console.log('[VISIBILITY] Page visible again, force reloading data...');
                            ChatLogOperations.load(true); // Silent reload
                        }
                    }
                });

                // NEW: Force reload on window focus
                window.addEventListener('focus', () => {
                    const chatlogSection = document.getElementById('chatlogSection');
                    if (chatlogSection && chatlogSection.style.display !== 'none' && !STATE.isLoading) {
                        console.log('[FOCUS] Window focused, checking for updates...');
                        ChatLogOperations.load(true);
                    }
                });
                            }
        };

        // Initialize
        EventHandlers.init();

        // Make available globally
        window.ChatLogOperations = ChatLogOperations;

        // Check if chatlog section is initially active
        const chatlogSection = document.getElementById('chatlogSection');
        if (chatlogSection && chatlogSection.style.display !== 'none') {
            ChatLogOperations.load();
            ChatLogOperations.startAutoRefresh();
        }
    });
})();