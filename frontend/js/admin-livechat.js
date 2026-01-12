// =========================
// ADMIN LIVE CHAT HANDLER
// =========================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const CONFIG = {
            API_BASE: 'http://127.0.0.1:5000/admin/live-chat',
            PAGE_SIZE: 50,
            AUTO_REFRESH_INTERVAL: 30000
        };

        const DOM = {
            tableBody: document.getElementById('livechatTableBody'),
            historyBody: document.getElementById('livechatHistoryBody'),
            status: document.getElementById('livechatStatus'),
            refreshBtn: document.getElementById('refreshLivechat'),
            section: document.getElementById('livechatSection'),
            statsOpen: document.getElementById('statsOpenRequests'),
            statsResolved: document.getElementById('statsResolvedRequests')
        };

        const STATE = {
            requests: [],
            history: [],
            isLoading: false,
            autoRefreshTimer: null,
            isSectionActive: false
        };

        const UI = {
            setStatus(msg, isError = false) {
                if (!DOM.status) return;
                DOM.status.textContent = msg;
                DOM.status.classList.toggle('error', isError);
            },

            updateStats() {
                if (DOM.statsOpen) {
                    DOM.statsOpen.textContent = STATE.requests.length;
                }
                if (DOM.statsResolved) {
                    DOM.statsResolved.textContent = STATE.history.length;
                }
            },

            renderRows(requests) {
                if (!DOM.tableBody) return;

                if (!requests.length) {
                    DOM.tableBody.innerHTML = `
                        <tr>
                            <td colspan="7" class="text-center text-muted">Tiada permintaan live chat terbuka.</td>
                        </tr>
                    `;
                    return;
                }

                DOM.tableBody.innerHTML = requests.map(req => `
                    <tr data-request-id="${req.id}">
                        <td><span class="id-badge">#${req.id}</span></td>
                        <td class="message-cell">
                            <div class="message-preview user-message-preview">
                                ${escapeHtml(truncateText(req.user_message || '', 60))}
                            </div>
                        </td>
                        <td class="message-cell">
                            <div class="message-preview bot-message-preview">
                                ${escapeHtml(truncateText(req.bot_response || '-', 60))}
                            </div>
                        </td>
                        <td><code class="session-code">${escapeHtml((req.session_id || '').substring(0, 8))}...</code></td>
                        <td class="date-cell">${formatDate(req.created_at)}</td>
                        <td class="text-center">
                            <button 
                                class="btn ghost btn-sm livechat-view-message" 
                                data-id="${req.id}"
                                title="Lihat Mesej Penuh"
                            >👁️ Lihat</button>
                            <button
                                class="btn warn btn-sm livechat-delete"
                                data-id="${req.id}"
                                title="Padam permintaan"
                                style="margin-left:8px;"
                            >🗑️ Padam</button>
                        </td>

                    </tr>
                `).join('');

                // Attach view / delete listeners (open requests)
                DOM.tableBody.querySelectorAll('.livechat-view-message').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        const request = requests.find(r => r.id === id);
                        if (request) showMessageModal(request);
                    });
                });

                DOM.tableBody.querySelectorAll('.livechat-delete').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        Controller.deleteRequest(id);
                    });
                });
            },

            renderHistory(rows) {
                if (!DOM.historyBody) return;
                if (!rows.length) {
                    DOM.historyBody.innerHTML = `
                        <tr>
                            <td colspan="7" class="text-center text-muted">Tiada rekod sejarah.</td>
                        </tr>
                    `;
                    return;
                }
                DOM.historyBody.innerHTML = rows.map(req => `
                    <tr data-request-id="${req.id}">
                        <td><span class="id-badge">#${req.id}</span></td>
                        <td class="message-cell">
                            <div class="message-preview user-message-preview">
                                ${escapeHtml(truncateText(req.user_message || '', 60))}
                            </div>
                        </td>
                        <td class="message-cell">
                            <div class="message-preview bot-message-preview">
                                ${escapeHtml(truncateText(req.bot_response || '-', 60))}
                            </div>
                        </td>
                        <td><code class="session-code">${escapeHtml((req.session_id || '').substring(0, 8))}...</code></td>
                        <td class="date-cell">${formatDate(req.updated_at || req.delivered_at || req.created_at)}</td>
                        <td class="text-center">
                            <button class="btn ghost btn-sm history-view" data-id="${req.id}">👁️ Lihat</button>
                            <button class="btn warn btn-sm history-delete" data-id="${req.id}" style="margin-left:8px;">🗑️ Padam</button>
                        </td>

                    </tr>
                `).join('');

                // Attach listeners for history view/delete
                DOM.historyBody.querySelectorAll('.history-view').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        const request = STATE.history.find(r => r.id === id);
                        if (request) showMessageModal(request);
                    });
                });

                DOM.historyBody.querySelectorAll('.history-delete').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        Controller.deleteRequest(id);
                    });
                });
            }
        };

        const API = {
            async fetchRequests(status = 'open', limit = 100, offset = 0) {
                const params = new URLSearchParams({
                    status: String(status),
                    limit: String(limit),
                    offset: String(offset),
                    _t: Date.now().toString()
                });
                console.log(`[API] Fetching live chat requests: ${CONFIG.API_BASE}?${params}`);
                const res = await fetch(`${CONFIG.API_BASE}?${params}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
                }
                return res.json();
            },

            async fetchHistory(limit = 100, offset = 0) {
                const params = new URLSearchParams({
                    limit: String(limit),
                    offset: String(offset),
                    _t: Date.now().toString()
                });
                console.log(`[API] Fetching live chat history: ${CONFIG.API_BASE}/history?${params}`);
                const res = await fetch(`${CONFIG.API_BASE}/history?${params}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
                }
                return res.json();
            },

            async respond(id, admin_response, admin_name = 'Admin') {
                console.log(`📤 Sending response for request #${id}...`);

                const res = await fetch(`${CONFIG.API_BASE}/${id}/respond`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        admin_response: admin_response.trim(),
                        admin_name
                    })
                });

                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${res.status}`);
                }

                const data = await res.json();
                console.log('✅ Response sent successfully:', data);
                return data;
            },

            async deleteRequest(id) {
                try {
                    const res = await fetch(`${CONFIG.API_BASE}/${encodeURIComponent(id)}`, {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' }
                    });

                    if (!res.ok) {
                        const errorData = await res.json().catch(() => ({}));
                        throw new Error(errorData.error || `HTTP ${res.status}`);
                    }

                    // Some servers return 204 No Content for successful deletes (no JSON body).
                    if (res.status === 204) {
                        return { success: true };
                    }

                    // Try to parse JSON, but fall back to success if parsing  fails.
                    const data = await res.json().catch(() => ({ success: true }));
                    return data;
                } catch (err) {
                    // Network / CORS / preflight failures surface as TypeError: Failed to fetch
                    console.error('🔒 Network/CORS error while deleting request:', err);
                    throw new Error('Network/CORS error while deleting. Check server CORS and that OPTIONS requests for DELETE return 200. Details: ' + (err.message || err));
                }
            }
        };

        const Controller = {
            async load(silent = false) {
                if (!DOM.section || DOM.section.style.display === 'none') {
                    console.log('⏸️ Live chat section not visible, skipping load');
                    return;
                }

                if (!silent) {
                    STATE.isLoading = true;
                    UI.setStatus('⏳ Memuat permintaan live chat...');
                }

                try {
                    console.log('📥 Loading live chat requests...');

                    // Load open requests
                    const data = await API.fetchRequests('open', CONFIG.PAGE_SIZE, 0);
                    console.log('📥 API Response:', data);

                    if (!data.success) {
                        throw new Error(data.error || 'Failed to fetch live chat requests');
                    }

                    STATE.requests = data.requests || [];

                    console.log(`✅ Loaded ${STATE.requests.length} open requests`);

                    UI.renderRows(STATE.requests);
                    UI.setStatus(`✅ ${STATE.requests.length} permintaan terbuka`);

                    // Load history separately
                    const hist = await API.fetchHistory(CONFIG.PAGE_SIZE, 0);
                    console.log('📥 History API Response:', hist);

                    if (!hist.success) {
                        console.warn('⚠️ Failed to load history:', hist.error);
                    } else {
                        STATE.history = hist.requests || [];
                        console.log(`✅ Loaded ${STATE.history.length} resolved requests`);
                        UI.renderHistory(STATE.history);
                    }

                    UI.updateStats();

                } catch (err) {
                    console.error('❌ Load error:', err);
                    console.error('❌ Error details:', err.message, err.stack);
                    if (!silent) {
                        const errorMsg = err.message || 'Gagal memuat data live chat';
                        UI.setStatus(`❌ ${errorMsg}`, true);
                        // Also show in console for debugging
                        console.error('❌ Full error object:', err);
                    }
                } finally {
                    if (!silent) {
                        STATE.isLoading = false;
                    }
                }
            },

            async sendResponse(id, text, sessionId) {
                if (!text || !text.trim()) {
                    alert('Sila masukkan jawapan.');
                    return;
                }

                const trimmedText = text.trim();
                console.log(`\n📤 SENDING ADMIN RESPONSE`);
                console.log(`   Request ID: ${id}`);
                console.log(`   Session ID: ${sessionId}`);
                console.log(`   Response: ${trimmedText.substring(0, 50)}...`);

                // Get admin name from localStorage or use default
                const adminName = localStorage.getItem('admin_name') || 'Admin';

                // Disable the send button to prevent double-clicking
                const sendBtn = DOM.tableBody?.querySelector(`.livechat-send[data-id="${id}"]`);
                const textarea = DOM.tableBody?.querySelector(`.livechat-reply[data-id="${id}"]`);

                if (sendBtn) {
                    sendBtn.disabled = true;
                    sendBtn.innerHTML = '⏳ Menghantar...';
                }

                UI.setStatus('⏳ Menghantar jawapan...');

                try {
                    const result = await API.respond(id, trimmedText, adminName);

                    if (result && result.success) {
                        console.log('✅ Response sent successfully!');

                        UI.setStatus('✅ Jawapan dihantar! Pengguna akan menerima dalam beberapa saat.');

                        // Show success notification
                        this.showSuccessNotification(id, sessionId);

                        // Remove the request from open list (optimistic update)
                        STATE.requests = STATE.requests.filter(r => r.id !== id);

                        // Update UI immediately
                        UI.renderRows(STATE.requests);
                        UI.updateStats();

                        // Reload after 2 seconds to sync with server
                        setTimeout(() => {
                            console.log('🔄 Reloading to sync with server...');
                            this.load(true);
                        }, 2000);

                    } else {
                        throw new Error(result?.error || 'Response failed');
                    }

                } catch (err) {
                    console.error('❌ Send response error:', err);
                    UI.setStatus(`❌ Gagal menghantar jawapan: ${err.message}`, true);
                    alert(`Gagal menghantar jawapan:\n${err.message}`);

                    // Re-enable button on error
                    if (sendBtn) {
                        sendBtn.disabled = false;
                        sendBtn.innerHTML = '📤 Hantar Jawapan';
                    }
                }
            },

            async deleteRequest(id) {
                if (!id) return;
                if (!confirm(`Padam permintaan live chat #${id}?`)) return;
                try {
                    UI.setStatus('⏳ Memadam permintaan...');
                    const result = await API.deleteRequest(id);
                    if (result && result.success) {
                        // Optimistic update
                        STATE.requests = STATE.requests.filter(r => r.id !== id);
                        STATE.history = STATE.history.filter(r => r.id !== id);
                        UI.renderRows(STATE.requests);
                        UI.renderHistory(STATE.history);
                        UI.updateStats();
                        UI.setStatus(`✅ Permintaan #${id} dipadam`);
                    } else {
                        throw new Error(result?.error || 'Gagal memadam rekod');
                    }
                } catch (err) {
                    console.error('❌ Delete error:', err);
                    UI.setStatus(`❌ ${err.message}`, true);
                    alert(`Gagal memadam: ${err.message}`);
                }
            },

            showSuccessNotification(requestId, sessionId) {
                // Create a success toast notification
                const notification = document.createElement('div');
                notification.className = 'success-notification';
                notification.innerHTML = `
                    <div class="notification-content">
                        <span class="notification-icon">✅</span>
                        <div class="notification-text">
                            <strong>Jawapan Dihantar!</strong>
                            <small>Request #${requestId} | Session: ${sessionId.substring(0, 8)}</small>
                        </div>
                    </div>
                `;

                document.body.appendChild(notification);

                // Auto-remove after 5 seconds
                setTimeout(() => {
                    notification.classList.add('fade-out');
                    setTimeout(() => notification.remove(), 300);
                }, 5000);
            },

            startAutoRefresh() {
                console.log('[AUTO-REFRESH] Starting live chat auto-refresh...');

                this.stopAutoRefresh();
                STATE.isSectionActive = true;

                const isSectionVisible = () => {
                    return DOM.section &&
                        DOM.section.style.display !== 'none' &&
                        DOM.section.offsetParent !== null;
                };

                STATE.autoRefreshTimer = setInterval(() => {
                    if (STATE.isSectionActive && isSectionVisible() && !STATE.isLoading) {
                        console.log('[AUTO-REFRESH] Refreshing live chat data...');
                        this.load(true);
                    }
                }, CONFIG.AUTO_REFRESH_INTERVAL);

                console.log(`[AUTO-REFRESH] Timer set to ${CONFIG.AUTO_REFRESH_INTERVAL}ms`);
            },

            stopAutoRefresh() {
                if (STATE.autoRefreshTimer) {
                    console.log('[AUTO-REFRESH] Stopping live chat auto-refresh');
                    clearInterval(STATE.autoRefreshTimer);
                    STATE.autoRefreshTimer = null;
                }
                STATE.isSectionActive = false;
            }
        };

        function formatDate(dt) {
            if (!dt) return '-';
            try {
                // Parse the datetime string directly without timezone conversion
                // Format: "2025-12-15 14:18:31" from database
                const parts = (typeof dt === 'string' ? dt : String(dt)).match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);

                if (parts) {
                    const [, year, month, day, hour, min] = parts;
                    const monthNames = [
                        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
                    ];
                    const monthName = monthNames[parseInt(month) - 1];
                    // Return the EXACT time from database without any conversion
                    return `${day} ${monthName} ${year}, ${hour}:${min}`;
                }

                // Fallback: try Date object if string parsing fails
                const d = new Date(dt);
                if (!isNaN(d.getTime())) {
                    return d.toLocaleString('ms-MY', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                }
            } catch (_) { }
            return dt;
        }

        function escapeHtml(str) {
            return (str || '').replace(/[&<>"']/g, m => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
            })[m] || m);
        }

        function truncateText(text, maxLength = 80) {
            if (!text) return '';
            return text.length > maxLength
                ? text.substring(0, maxLength) + '...'
                : text;
        }

        function showMessageModal(request) {
            // Create modal if it doesn't exist
            let modal = document.getElementById('livechatMessageModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'livechatMessageModal';
                modal.className = 'modal-overlay';
                modal.innerHTML = `
                    <div class="modal-content" style="max-width: 700px; max-height: 90vh; overflow-y: auto;">
                        <div class="modal-header">
                            <h2>📋 Butiran Live Chat</h2>
                            <button class="modal-close" id="closeMessageModal">&times;</button>
                        </div>
                        <div class="modal-body" id="messageModalBody"></div>
                    </div>
                `;
                document.body.appendChild(modal);

                // Close button handler
                document.getElementById('closeMessageModal').addEventListener('click', () => {
                    modal.style.display = 'none';
                });

                // Close on overlay click
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        modal.style.display = 'none';
                    }
                });
            }

            // Populate modal content
            const modalBody = document.getElementById('messageModalBody');

            const isOpenRequest = STATE.requests.some(r => r.id === request.id);

            let adminSectionHtml = '';
            if (isOpenRequest) {
                adminSectionHtml = `
                    <div style="padding: 16px; background: #fff7ed; border-radius: 12px; border-left: 4px solid #f59e0b;">
                        <h3 style="margin: 0 0 12px 0; color: #92400e; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">✏️ Jawapan Admin</h3>
                        <textarea id="modalAdminResponse" rows="6" style="width:100%; min-height: 120px; font-size: 14px; line-height: 1.5;">${escapeHtml(request.admin_response || '')}</textarea>
                        <button id="modalSendResponse" class="btn primary" style="margin-top: 12px;">📤 Hantar Jawapan</button>
                    </div>
                `;
            } else {
                adminSectionHtml = `
                    <div style="padding: 16px; background: #f8fafc; border-radius: 12px; border-left: 4px solid #9ca3af;">
                        <h3 style="margin: 0 0 12px 0; color: #374151; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">✏️ Jawapan Admin</h3>
                        <p style="margin: 0; color: #1f2937; font-size: 15px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;">${escapeHtml(request.admin_response || '-')}</p>
                        ${request.admin_name ? `<small class="admin-name">- ${escapeHtml(request.admin_name)}</small>` : ''}
                    </div>
                `;
            }

            modalBody.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 24px;">
                    <div>
                        <h3 style="margin: 0 0 8px 0; color: #1f2937; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">ID & Session</h3>
                        <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                            <div><strong>Request ID:</strong> <span class="id-badge">#${request.id}</span></div>
                            <div><strong>Session:</strong> <code class="session-code">${escapeHtml(request.session_id || 'N/A')}</code></div>
                            <div><strong>Tarikh:</strong> ${formatDate(request.created_at)}</div>
                        </div>
                    </div>
                    
                    <div style="padding: 16px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 12px; border-left: 4px solid #3b82f6;">
                        <h3 style="margin: 0 0 12px 0; color: #1e40af; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">💬 Soalan Pengguna</h3>
                        <p style="margin: 0; color: #1f2937; font-size: 15px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;">${escapeHtml(request.user_message || 'Tiada soalan')}</p>
                    </div>
                    
                    <div style="padding: 16px; background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 12px; border-left: 4px solid #10b981;">
                        <h3 style="margin: 0 0 12px 0; color: #065f46; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">🤖 Jawapan Bot</h3>
                        <p style="margin: 0; color: #1f2937; font-size: 15px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;">${escapeHtml(request.bot_response || 'Tiada jawapan')}</p>
                    </div>

                    ${adminSectionHtml}
                </div>
            `;

            // Attach modal send handler (if open request)
            if (isOpenRequest) {
                const modalSendBtn = document.getElementById('modalSendResponse');
                const modalTextarea = document.getElementById('modalAdminResponse');

                if (modalSendBtn && modalTextarea) {
                    modalSendBtn.addEventListener('click', async () => {
                        const text = modalTextarea.value || '';
                        if (!text.trim()) {
                            alert('Sila masukkan jawapan.');
                            return;
                        }

                        modalSendBtn.disabled = true;
                        modalSendBtn.innerText = '⏳ Menghantar...';

                        // Use Controller.sendResponse which handles optimistic UI updates
                        await Controller.sendResponse(request.id, text, request.session_id || '');

                        // If the request was removed from open list, close modal
                        const stillOpen = STATE.requests.some(r => r.id === request.id);
                        if (!stillOpen) {
                            modal.style.display = 'none';
                        } else {
                            modalSendBtn.disabled = false;
                            modalSendBtn.innerText = '📤 Hantar Jawapan';
                        }
                    });

                    // Ctrl/Cmd+Enter to send from modal textarea
                    modalTextarea.addEventListener('keydown', (e) => {
                        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                            const btn = document.getElementById('modalSendResponse');
                            if (btn) btn.click();
                        }
                    });
                }
            }

            // Show modal
            modal.style.display = 'flex';
        }

        function attachEvents() {
            if (DOM.refreshBtn) {
                DOM.refreshBtn.addEventListener('click', () => {
                    console.log('🔄 Manual refresh triggered');
                    Controller.load();
                });
            }

            if (DOM.tableBody) {
                // Reply UI removed from inline rows and moved into the "Lihat" modal.
                // Modal send handler is attached inside showMessageModal when appropriate.
            }

            // Monitor section visibility
            const observer = new MutationObserver(() => {
                const isVisible = DOM.section &&
                    DOM.section.style.display !== 'none' &&
                    DOM.section.offsetParent !== null;

                if (isVisible && !STATE.isSectionActive) {
                    console.log('[OBSERVER] Live chat section became visible');
                    STATE.isSectionActive = true;
                    Controller.load();
                    Controller.startAutoRefresh();
                } else if (!isVisible && STATE.isSectionActive) {
                    console.log('[OBSERVER] Live chat section hidden');
                    Controller.stopAutoRefresh();
                }
            });

            if (DOM.section) {
                observer.observe(DOM.section, {
                    attributes: true,
                    attributeFilter: ['style', 'class']
                });
            }
        }

        attachEvents();

        // Expose globally for navigation handler
        window.LiveChatAdmin = {
            load: () => Controller.load(),
            startAutoRefresh: () => Controller.startAutoRefresh(),
            stopAutoRefresh: () => Controller.stopAutoRefresh()
        };

        console.log('✅ Admin Live Chat Handler initialized');
    });
})();