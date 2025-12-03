// =========================
// ADMIN CHAT LOG HANDLER
// =========================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const CONFIG = {
            API_BASE: 'http://127.0.0.1:5000/admin/chat-logs',
            PAGE_SIZE: 50
        };

        const DOM = {
            chatlogTableBody: document.getElementById('chatlogTableBody'),
            chatlogEmptyState: document.getElementById('chatlogEmptyState'),
            chatlogStatus: document.getElementById('chatlogStatus'),
            refreshChatLogs: document.getElementById('refreshChatLogs'),
            chatlogSearch: document.getElementById('chatlogSearch'),
            chatlogPagination: document.getElementById('chatlogPagination'),
            exportChatLogsBtn: document.getElementById('exportChatLogsBtn'),
            printChatLogsBtn: document.getElementById('printChatLogsBtn')
        };

        let STATE = {
            logs: [],
            filteredLogs: [],
            currentPage: 1,
            totalPages: 1,
            isLoading: false
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
                const date = new Date(dateStr);
                return date.toLocaleString('ms-MY', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            },

            truncateText(text, maxLength = 100) {
                if (!text) return '';
                return text.length > maxLength 
                    ? text.substring(0, maxLength) + '...' 
                    : text;
            },

            renderLogs(logs) {
                if (!DOM.chatlogTableBody) return;

                if (logs.length === 0) {
                    DOM.chatlogTableBody.innerHTML = '';
                    if (DOM.chatlogEmptyState) DOM.chatlogEmptyState.style.display = 'block';
                    return;
                }

                if (DOM.chatlogEmptyState) DOM.chatlogEmptyState.style.display = 'none';

                DOM.chatlogTableBody.innerHTML = logs.map(log => `
                    <tr>
                        <td><span class="id-badge">#${log.id_log}</span></td>
                        <td>${log.id_user != null ? `#${log.id_user}` : '-'}</td>
                        <td><code style="font-size: 11px;">${this.escapeHtml((log.session_id || '').substring(0, 12))}...</code></td>
                        <td class="chatlog-message">
                            <div class="message-preview">${this.escapeHtml(this.truncateText(log.user_message, 80))}</div>
                        </td>
                        <td class="chatlog-message">
                            <div class="message-preview">${this.escapeHtml(this.truncateText(log.bot_response, 80))}</div>
                        </td>
                        <td class="date-cell">${this.formatDate(log.created_at)}</td>
                        <td>
                            <div class="admin-actions">
                                <button class="btn ghost btn-sm" data-action="view" data-id="${log.id_log}" title="Papar Butiran">
                                    👁️ Papar
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('');
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

                DOM.chatlogPagination.innerHTML = `
                    <div class="pagination-info">
                        Page ${currentPage} of ${totalPages} (${STATE.filteredLogs.length} logs)
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
            }
        };

        const APIService = {
            async fetchChatLogs(limit = 1000, offset = 0, search = '') {
                const params = new URLSearchParams({
                    limit: limit.toString(),
                    offset: offset.toString()
                });

                const res = await fetch(`${CONFIG.API_BASE}?${params}`);

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

                return data;
            },

            async getChatLog(id) {
                const res = await fetch(`${CONFIG.API_BASE}/${id}`);
                if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                return await res.json();
            }
        };

        const ChatLogOperations = {
            async load() {
                try {
                    UIManager.showLoading(true);
                    UIManager.updateStatus('⏳ Memuat chat logs...');

                    const data = await APIService.fetchChatLogs();
                    STATE.logs = data.logs || [];

                    this.applyFilters();

                    if (STATE.logs.length > 0) {
                        UIManager.updateStatus(`✅ ${STATE.logs.length} chat logs loaded`);
                    } else {
                        UIManager.updateStatus('ℹ️ Tiada chat logs ditemui', false);
                    }
                } catch (error) {
                    console.error('Error loading chat logs:', error);
                    UIManager.updateStatus(`❌ Error: ${error.message}`, true);
                    STATE.logs = [];
                    this.applyFilters();
                } finally {
                    UIManager.showLoading(false);
                }
            },

            applyFilters() {
                const search = (DOM.chatlogSearch?.value || '').toLowerCase();

                STATE.filteredLogs = STATE.logs.filter(log => {
                    if (!search) return true;

                    const searchableText = [
                        log.user_message,
                        log.bot_response,
                        log.session_id,
                        log.id_user?.toString()
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
                            <h2>Chat Log Details</h2>
                            <span class="id-badge">#${log.id_log}</span>
                        </div>
                        
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>Log ID:</label>
                                <span class="id-badge">#${log.id_log}</span>
                            </div>
                            <div class="detail-item">
                                <label>User ID:</label>
                                <span>${log.id_user != null ? `#${log.id_user}` : 'N/A'}</span>
                            </div>
                            <div class="detail-item full-width">
                                <label>Session ID:</label>
                                <code>${UIManager.escapeHtml(log.session_id || 'N/A')}</code>
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
                            <div class="detail-item">
                                <label>Timestamp:</label>
                                <span>${UIManager.formatDate(log.created_at)}</span>
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
            }
        };

        const PrintManager = {
            printAll() {
                if (STATE.filteredLogs.length === 0) {
                    alert('No chat logs to print');
                    return;
                }

                const printWindow = window.open('', '_blank');
                const content = this.generatePrintContent(STATE.filteredLogs);

                printWindow.document.write(content);
                printWindow.document.close();
                printWindow.focus();

                setTimeout(() => {
                    printWindow.print();
                }, 500);
            },

            generatePrintContent(logs) {
                const now = new Date().toLocaleString('ms-MY');

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
                            .log-item { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; page-break-inside: avoid; }
                            .log-header { display: flex; justify-content: space-between; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
                            .log-id { font-weight: bold; color: #006a4e; }
                            .log-date { color: #666; font-size: 12px; }
                            .message-section { margin: 10px 0; }
                            .message-label { font-weight: bold; color: #333; margin-bottom: 5px; }
                            .user-message { background: #f0f9ff; padding: 10px; border-radius: 6px; margin-bottom: 10px; }
                            .bot-message { background: #f0fdf4; padding: 10px; border-radius: 6px; }
                            .footer { margin-top: 30px; text-align: center; color: #666; font-size: 12px; }
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
                    DOM.chatlogSearch.addEventListener('input', () => {
                        ChatLogOperations.applyFilters();
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

                // Print
                if (DOM.printChatLogsBtn) {
                    DOM.printChatLogsBtn.addEventListener('click', () => {
                        PrintManager.printAll();
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
                        }
                    });
                }
            }
        };

        // Initialize
        EventHandlers.init();

        // Make available globally
        window.ChatLogOperations = ChatLogOperations;
    });
})();