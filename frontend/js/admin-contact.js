// =========================
// ADMIN CONTACT REQUEST HANDLER
// =========================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const CONFIG = {
            API_BASE: 'http://127.0.0.1:5000/admin/contact-requests',
            PAGE_SIZE: 50,
            AUTO_REFRESH_INTERVAL: 30000
        };

        const DOM = {
            section: document.getElementById('contactRequestsSection'),
            status: document.getElementById('contactStatus'),
            refreshBtn: document.getElementById('refreshContacts'),
            
            // Stats
            statsPending: document.getElementById('statsPendingContacts'),
            statsContacted: document.getElementById('statsContactedContacts'),
            statsResolved: document.getElementById('statsResolvedContacts'),
            statsTotal: document.getElementById('statsTotalContacts'),
            
            // Tables
            contactTableBody: document.getElementById('contactTableBody'),
            historyTableBody: document.getElementById('historyTableBody'),
            
            // Filters
            contactSearch: document.getElementById('contactSearch'),
            contactMethodFilter: document.getElementById('contactMethodFilter'),
            contactTriggerFilter: document.getElementById('contactTriggerFilter'),
            historySearch: document.getElementById('historySearch'),
            historyStatusFilter: document.getElementById('historyStatusFilter'),
            
            // Tabs
            tabBtns: document.querySelectorAll('.tab-btn'),
            pendingTab: document.getElementById('pendingTab'),
            historyTab: document.getElementById('historyTab'),
            pendingBadge: document.getElementById('pendingBadge'),
            
            // Office status
            officeStatus: document.getElementById('officeStatusIndicator'),
            
            // Empty states
            contactEmptyState: document.getElementById('contactEmptyState'),
            historyEmptyState: document.getElementById('historyEmptyState')
        };

        const STATE = {
            pendingRequests: [],
            historyRequests: [],
            currentTab: 'pending',
            isLoading: false,
            autoRefreshTimer: null,
            isSectionActive: false,
            selectedRequestId: null
        };

        const UI = {
            setStatus(msg, isError = false) {
                if (!DOM.status) return;
                DOM.status.textContent = msg;
                DOM.status.classList.toggle('error', isError);
            },

            updateStats() {
                const pending = STATE.pendingRequests.length;
                const contacted = STATE.historyRequests.filter(r => r.status === 'contacted').length;
                const resolved = STATE.historyRequests.filter(r => r.status === 'resolved').length;
                const total = pending + contacted + resolved;
                
                if (DOM.statsPending) DOM.statsPending.textContent = pending;
                if (DOM.statsContacted) DOM.statsContacted.textContent = contacted;
                if (DOM.statsResolved) DOM.statsResolved.textContent = resolved;
                if (DOM.statsTotal) DOM.statsTotal.textContent = total;
                if (DOM.pendingBadge) DOM.pendingBadge.textContent = pending;
            },

            updateOfficeStatus(isOpen) {
                if (!DOM.officeStatus) return;
                
                const dot = DOM.officeStatus.querySelector('.status-dot');
                const text = DOM.officeStatus.querySelector('.status-text');
                
                if (isOpen) {
                    dot.style.background = '#10b981';
                    text.textContent = 'Waktu Operasi';
                } else {
                    dot.style.background = '#ef4444';
                    text.textContent = 'Tutup';
                }
            },

            renderPendingRequests(requests) {
                if (!DOM.contactTableBody) return;

                // Apply filters
                let filtered = this.applyFilters(requests, {
                    search: DOM.contactSearch?.value || '',
                    method: DOM.contactMethodFilter?.value || '',
                    trigger: DOM.contactTriggerFilter?.value || ''
                });

                if (!filtered.length) {
                    DOM.contactTableBody.innerHTML = '';
                    if (DOM.contactEmptyState) DOM.contactEmptyState.style.display = 'flex';
                    return;
                }

                if (DOM.contactEmptyState) DOM.contactEmptyState.style.display = 'none';

                DOM.contactTableBody.innerHTML = filtered.map(req => `
                    <tr data-request-id="${req.id}">
                        <td><span class="id-badge">#${req.id}</span></td>
                        <td><strong>${escapeHtml(req.name)}</strong></td>
                        <td>
                            <a href="tel:${escapeHtml(req.phone)}" class="contact-link">
                                ${escapeHtml(req.phone)}
                            </a>
                        </td>
                        <td>
                            ${req.email ? `<a href="mailto:${escapeHtml(req.email)}" class="contact-link">${escapeHtml(req.email)}</a>` : '-'}
                        </td>
                        <td class="question-cell">
                            <div class="question-preview" title="${escapeHtml(req.question)}">
                                ${escapeHtml(truncateText(req.question, 80))}
                            </div>
                        </td>
                        <td>
                            <span class="method-badge method-${req.preferred_contact_method}">
                                ${getMethodIcon(req.preferred_contact_method)} ${capitalizeFirst(req.preferred_contact_method)}
                            </span>
                        </td>
                        <td class="date-cell">${formatDate(req.created_at)}</td>
                        <td class="action-cell">
                            <button class="btn ghost btn-sm view-contact" data-id="${req.id}" title="Lihat Butiran">
                                👁️ Lihat
                            </button>
                            <button class="btn primary btn-sm mark-contacted" data-id="${req.id}" title="Tanda Dihubungi">
                                ✅ Hubungi
                            </button>
                            <button class="btn warn btn-sm delete-contact" data-id="${req.id}" title="Padam">
                                🗑️
                            </button>
                        </td>
                    </tr>
                `).join('');

                this.attachPendingListeners();
            },

            renderHistoryRequests(requests) {
                if (!DOM.historyTableBody) return;

                // Apply filters
                let filtered = requests.filter(req => {
                    const searchTerm = (DOM.historySearch?.value || '').toLowerCase();
                    const statusFilter = DOM.historyStatusFilter?.value || '';
                    
                    if (statusFilter && req.status !== statusFilter) return false;
                    
                    if (searchTerm) {
                        return req.name.toLowerCase().includes(searchTerm) ||
                               req.phone.includes(searchTerm) ||
                               (req.email && req.email.toLowerCase().includes(searchTerm));
                    }
                    
                    return true;
                });

                if (!filtered.length) {
                    DOM.historyTableBody.innerHTML = '';
                    if (DOM.historyEmptyState) DOM.historyEmptyState.style.display = 'flex';
                    return;
                }

                if (DOM.historyEmptyState) DOM.historyEmptyState.style.display = 'none';

                DOM.historyTableBody.innerHTML = filtered.map(req => `
                    <tr data-request-id="${req.id}">
                        <td><span class="id-badge">#${req.id}</span></td>
                        <td><strong>${escapeHtml(req.name)}</strong></td>
                        <td>
                            <a href="tel:${escapeHtml(req.phone)}" class="contact-link">
                                ${escapeHtml(req.phone)}
                            </a>
                        </td>
                        <td class="question-cell">
                            <div class="question-preview" title="${escapeHtml(req.question)}">
                                ${escapeHtml(truncateText(req.question, 60))}
                            </div>
                        </td>
                        <td>
                            <span class="method-badge method-${req.contact_method_used || req.preferred_contact_method}">
                                ${capitalizeFirst(req.contact_method_used || req.preferred_contact_method)}
                            </span>
                        </td>
                        <td>
                            <span class="status-badge status-${req.status}">
                                ${req.status === 'contacted' ? '✅ Dihubungi' : '🎯 Selesai'}
                            </span>
                        </td>
                        <td class="date-cell">${formatDate(req.contacted_at || req.updated_at)}</td>
                        <td class="action-cell">
                            <button class="btn ghost btn-sm view-history" data-id="${req.id}" title="Lihat Butiran">
                                👁️ Lihat
                            </button>
                            <button class="btn warn btn-sm delete-history" data-id="${req.id}" title="Padam">
                                🗑️
                            </button>
                        </td>
                    </tr>
                `).join('');

                this.attachHistoryListeners();
            },

            applyFilters(requests, filters) {
                return requests.filter(req => {
                    // Search filter
                    if (filters.search) {
                        const searchLower = filters.search.toLowerCase();
                        const matchSearch = req.name.toLowerCase().includes(searchLower) ||
                                          req.phone.includes(searchLower) ||
                                          (req.email && req.email.toLowerCase().includes(searchLower)) ||
                                          req.question.toLowerCase().includes(searchLower);
                        if (!matchSearch) return false;
                    }
                    
                    // Method filter
                    if (filters.method && req.preferred_contact_method !== filters.method) {
                        return false;
                    }
                    
                    // Trigger filter
                    if (filters.trigger && req.trigger_type !== filters.trigger) {
                        return false;
                    }
                    
                    return true;
                });
            },

            attachPendingListeners() {
                // View buttons
                DOM.contactTableBody.querySelectorAll('.view-contact').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        const request = STATE.pendingRequests.find(r => r.id === id);
                        if (request) showContactDetail(request);
                    });
                });

                // Mark contacted buttons
                DOM.contactTableBody.querySelectorAll('.mark-contacted').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        const request = STATE.pendingRequests.find(r => r.id === id);
                        if (request) showMarkContactedModal(request);
                    });
                });

                // Delete buttons
                DOM.contactTableBody.querySelectorAll('.delete-contact').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        Controller.deleteRequest(id);
                    });
                });
            },

            attachHistoryListeners() {
                // View buttons
                DOM.historyTableBody.querySelectorAll('.view-history').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        const request = STATE.historyRequests.find(r => r.id === id);
                        if (request) showContactDetail(request);
                    });
                });

                // Delete buttons
                DOM.historyTableBody.querySelectorAll('.delete-history').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const id = parseInt(btn.getAttribute('data-id'));
                        Controller.deleteRequest(id);
                    });
                });
            }
        };

        const API = {
            async fetchRequests(status = 'pending', limit = 100, offset = 0) {
                const params = new URLSearchParams({
                    status: String(status),
                    limit: String(limit),
                    offset: String(offset),
                    _t: Date.now().toString()
                });
                
                console.log(`[API] Fetching contact requests: ${CONFIG.API_BASE}?${params}`);
                
                const res = await fetch(`${CONFIG.API_BASE}?${params}`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
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
                
                console.log(`[API] Fetching contact history: ${CONFIG.API_BASE}/history?${params}`);
                
                const res = await fetch(`${CONFIG.API_BASE}/history?${params}`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${res.status}: ${res.statusText}`);
                }
                
                return res.json();
            },

            async markContacted(id, data) {
                console.log(`📞 Marking request #${id} as contacted...`);
                
                const res = await fetch(`${CONFIG.API_BASE}/${id}/mark-contacted`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${res.status}`);
                }
                
                const result = await res.json();
                console.log('✅ Marked as contacted:', result);
                return result;
            },

            async deleteRequest(id) {
                const res = await fetch(`${CONFIG.API_BASE}/${encodeURIComponent(id)}`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (!res.ok) {
                    const errorData = await res.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${res.status}`);
                }
                
                if (res.status === 204) {
                    return { success: true };
                }
                
                return res.json().catch(() => ({ success: true }));
            },

            async checkOfficeHours() {
                try {
                    const res = await fetch('http://127.0.0.1:5000/contact-request/health');
                    const data = await res.json();
                    return data.office_hours === 'open';
                } catch (e) {
                    console.error('Office hours check failed:', e);
                    return false;
                }
            }
        };

        const Controller = {
            async load(silent = false) {
                if (!DOM.section || DOM.section.style.display === 'none') {
                    console.log('⏸️ Contact requests section not visible, skipping load');
                    return;
                }

                if (!silent) {
                    STATE.isLoading = true;
                    UI.setStatus('⏳ Memuat permintaan...');
                }

                try {
                    console.log('📥 Loading contact requests...');

                    // Load pending requests
                    const pendingData = await API.fetchRequests('pending', CONFIG.PAGE_SIZE, 0);
                    
                    if (!pendingData.success) {
                        throw new Error(pendingData.error || 'Failed to fetch pending requests');
                    }

                    STATE.pendingRequests = pendingData.requests || [];
                    console.log(`✅ Loaded ${STATE.pendingRequests.length} pending requests`);

                    // Load history
                    const historyData = await API.fetchHistory(CONFIG.PAGE_SIZE, 0);
                    
                    if (historyData.success) {
                        STATE.historyRequests = historyData.requests || [];
                        console.log(`✅ Loaded ${STATE.historyRequests.length} history requests`);
                    }

                    // Update UI
                    UI.renderPendingRequests(STATE.pendingRequests);
                    UI.renderHistoryRequests(STATE.historyRequests);
                    UI.updateStats();
                    
                    // Check office hours
                    const isOfficeOpen = await API.checkOfficeHours();
                    UI.updateOfficeStatus(isOfficeOpen);

                    UI.setStatus(`✅ ${STATE.pendingRequests.length} permintaan menunggu`);

                } catch (err) {
                    console.error('❌ Load error:', err);
                    if (!silent) {
                        UI.setStatus(`❌ ${err.message}`, true);
                    }
                } finally {
                    if (!silent) {
                        STATE.isLoading = false;
                    }
                }
            },

            async markContacted(id, contactData) {
                try {
                    UI.setStatus('⏳ Menandai sebagai dihubungi...');
                    
                    const result = await API.markContacted(id, contactData);
                    
                    if (result && result.success) {
                        // Remove from pending, reload data
                        STATE.pendingRequests = STATE.pendingRequests.filter(r => r.id !== id);
                        
                        UI.renderPendingRequests(STATE.pendingRequests);
                        UI.setStatus('✅ Ditanda sebagai dihubungi');
                        
                        // Reload after 1 second
                        setTimeout(() => this.load(true), 1000);
                        
                        return true;
                    } else {
                        throw new Error(result?.error || 'Failed to mark as contacted');
                    }
                } catch (err) {
                    console.error('❌ Mark contacted error:', err);
                    UI.setStatus(`❌ ${err.message}`, true);
                    alert(`Gagal menandai: ${err.message}`);
                    return false;
                }
            },

            async deleteRequest(id) {
                if (!confirm(`Padam permintaan #${id}?`)) return;
                
                try {
                    UI.setStatus('⏳ Memadam...');
                    
                    const result = await API.deleteRequest(id);
                    
                    if (result && result.success) {
                        STATE.pendingRequests = STATE.pendingRequests.filter(r => r.id !== id);
                        STATE.historyRequests = STATE.historyRequests.filter(r => r.id !== id);
                        
                        UI.renderPendingRequests(STATE.pendingRequests);
                        UI.renderHistoryRequests(STATE.historyRequests);
                        UI.updateStats();
                        
                        UI.setStatus(`✅ Permintaan #${id} dipadam`);
                    } else {
                        throw new Error(result?.error || 'Failed to delete');
                    }
                } catch (err) {
                    console.error('❌ Delete error:', err);
                    UI.setStatus(`❌ ${err.message}`, true);
                    alert(`Gagal memadam: ${err.message}`);
                }
            },

            startAutoRefresh() {
                console.log('[AUTO-REFRESH] Starting contact requests auto-refresh...');
                
                this.stopAutoRefresh();
                STATE.isSectionActive = true;

                STATE.autoRefreshTimer = setInterval(() => {
                    if (STATE.isSectionActive && !STATE.isLoading) {
                        console.log('[AUTO-REFRESH] Refreshing contact requests...');
                        this.load(true);
                    }
                }, CONFIG.AUTO_REFRESH_INTERVAL);
            },

            stopAutoRefresh() {
                if (STATE.autoRefreshTimer) {
                    clearInterval(STATE.autoRefreshTimer);
                    STATE.autoRefreshTimer = null;
                }
                STATE.isSectionActive = false;
            }
        };

        // Helper Functions
        function formatDate(dt) {
            if (!dt) return '-';
            try {
                const parts = (typeof dt === 'string' ? dt : String(dt)).match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/);
                
                if (parts) {
                    const [, year, month, day, hour, min] = parts;
                    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ogos', 'Sep', 'Okt', 'Nov', 'Dis'];
                    return `${day} ${monthNames[parseInt(month) - 1]} ${year}, ${hour}:${min}`;
                }
                
                return new Date(dt).toLocaleString('ms-MY');
            } catch (_) {
                return dt;
            }
        }

        function escapeHtml(str) {
            return (str || '').replace(/[&<>"']/g, m => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
            })[m] || m);
        }

        function truncateText(text, maxLength = 80) {
            if (!text) return '';
            return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
        }

        function capitalizeFirst(str) {
            if (!str) return '';
            return str.charAt(0).toUpperCase() + str.slice(1);
        }

        function getMethodIcon(method) {
            const icons = {
                whatsapp: '📞',
                phone: '☎️',
                email: '📧'
            };
            return icons[method] || '📞';
        }

        function showContactDetail(request) {
            const modal = document.getElementById('contactDetailModal');
            const body = document.getElementById('contactDetailBody');
            
            if (!modal || !body) return;
            
            body.innerHTML = `
                <div class="detail-grid">
                    <div class="detail-section">
                        <h4>📋 Maklumat Asas</h4>
                        <table class="detail-table">
                            <tr>
                                <td><strong>ID:</strong></td>
                                <td>#${request.id}</td>
                            </tr>
                            <tr>
                                <td><strong>Nama:</strong></td>
                                <td>${escapeHtml(request.name)}</td>
                            </tr>
                            <tr>
                                <td><strong>Telefon:</strong></td>
                                <td><a href="tel:${escapeHtml(request.phone)}">${escapeHtml(request.phone)}</a></td>
                            </tr>
                            <tr>
                                <td><strong>Email:</strong></td>
                                <td>${request.email ? `<a href="mailto:${escapeHtml(request.email)}">${escapeHtml(request.email)}</a>` : '-'}</td>
                            </tr>
                            <tr>
                                <td><strong>Kaedah Pilihan:</strong></td>
                                <td><span class="method-badge method-${request.preferred_contact_method}">${getMethodIcon(request.preferred_contact_method)} ${capitalizeFirst(request.preferred_contact_method)}</span></td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="detail-section">
                        <h4>💬 Soalan</h4>
                        <div class="detail-question">
                            ${escapeHtml(request.question)}
                        </div>
                    </div>
                    
                    ${request.trigger_type ? `
                    <div class="detail-section">
                        <h4>🎯 Trigger Type</h4>
                        <span class="trigger-badge">${getTriggerLabel(request.trigger_type)}</span>
                    </div>
                    ` : ''}
                    
                    ${request.admin_notes ? `
                    <div class="detail-section">
                        <h4>📝 Nota Admin</h4>
                        <div class="detail-notes">
                            ${escapeHtml(request.admin_notes)}
                        </div>
                        ${request.contacted_by ? `<p><em>- ${escapeHtml(request.contacted_by)}</em></p>` : ''}
                    </div>
                    ` : ''}
                    
                    <div class="detail-section">
                        <h4>📅 Tarikh</h4>
                        <table class="detail-table">
                            <tr>
                                <td><strong>Dibuat:</strong></td>
                                <td>${formatDate(request.created_at)}</td>
                            </tr>
                            ${request.contacted_at ? `
                            <tr>
                                <td><strong>Dihubungi:</strong></td>
                                <td>${formatDate(request.contacted_at)}</td>
                            </tr>
                            ` : ''}
                        </table>
                    </div>
                </div>
            `;
            
            modal.style.display = 'flex';
        }

        function showMarkContactedModal(request) {
            const modal = document.getElementById('markContactedModal');
            if (!modal) return;
            
            STATE.selectedRequestId = request.id;
            
            // Pre-fill with preferred method
            const methodSelect = document.getElementById('contactedMethodSelect');
            if (methodSelect) {
                methodSelect.value = request.preferred_contact_method;
            }
            
            // Load admin name from localStorage
            const adminInput = document.getElementById('contactedByInput');
            if (adminInput) {
                adminInput.value = localStorage.getItem('admin_name') || 'Admin';
            }
            
            modal.style.display = 'flex';
        }

        function getTriggerLabel(trigger) {
            const labels = {
                explicit_request: '🆘 Permintaan Terus',
                confusion: '❓ Keliru',
                repetition: '🔄 Soalan Berulang',
                complexity: '🎯 Kompleks',
                low_confidence: '📉 Keyakinan Rendah'
            };
            return labels[trigger] || trigger;
        }

        // Event Listeners
        function attachEvents() {
            // Refresh button
            if (DOM.refreshBtn) {
                DOM.refreshBtn.addEventListener('click', () => {
                    console.log('🔄 Manual refresh triggered');
                    Controller.load();
                });
            }

            // Tab switching
            DOM.tabBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const tab = btn.getAttribute('data-tab');
                    
                    // Update active states
                    DOM.tabBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    
                    // Show/hide tabs
                    if (DOM.pendingTab) DOM.pendingTab.classList.toggle('active', tab === 'pending');
                    if (DOM.historyTab) DOM.historyTab.classList.toggle('active', tab === 'history');
                    
                    STATE.currentTab = tab;
                });
            });

            // Search and filter inputs
            if (DOM.contactSearch) {
                DOM.contactSearch.addEventListener('input', () => {
                    UI.renderPendingRequests(STATE.pendingRequests);
                });
            }

            if (DOM.contactMethodFilter) {
                DOM.contactMethodFilter.addEventListener('change', () => {
                    UI.renderPendingRequests(STATE.pendingRequests);
                });
            }

            if (DOM.contactTriggerFilter) {
                DOM.contactTriggerFilter.addEventListener('change', () => {
                    UI.renderPendingRequests(STATE.pendingRequests);
                });
            }

            if (DOM.historySearch) {
                DOM.historySearch.addEventListener('input', () => {
                    UI.renderHistoryRequests(STATE.historyRequests);
                });
            }

            if (DOM.historyStatusFilter) {
                DOM.historyStatusFilter.addEventListener('change', () => {
                    UI.renderHistoryRequests(STATE.historyRequests);
                });
            }

            // Mark contacted confirmation
            const confirmBtn = document.getElementById('confirmMarkContactedBtn');
            if (confirmBtn) {
                confirmBtn.addEventListener('click', async () => {
                    const method = document.getElementById('contactedMethodSelect').value;
                    const notes = document.getElementById('adminNotesTextarea').value.trim();
                    const contactedBy = document.getElementById('contactedByInput').value.trim() || 'Admin';
                    
                    // Save admin name to localStorage
                    localStorage.setItem('admin_name', contactedBy);
                    
                    const success = await Controller.markContacted(STATE.selectedRequestId, {
                        contact_method_used: method,
                        admin_notes: notes,
                        contacted_by: contactedBy
                    });
                    
                    if (success) {
                        closeMarkContactedModal();
                    }
                });
            }
        }

        window.closeContactDetailModal = function() {
            const modal = document.getElementById('contactDetailModal');
            if (modal) modal.style.display = 'none';
        };

        window.closeMarkContactedModal = function() {
            const modal = document.getElementById('markContactedModal');
            if (modal) {
                modal.style.display = 'none';
                // Reset form
                document.getElementById('adminNotesTextarea').value = '';
            }
        };

        attachEvents();

        // Expose globally
        window.ContactRequestAdmin = {
            load: () => Controller.load(),
            startAutoRefresh: () => Controller.startAutoRefresh(),
            stopAutoRefresh: () => Controller.stopAutoRefresh()
        };

        console.log('✅ Admin Contact Request Handler initialized');
    });
})();