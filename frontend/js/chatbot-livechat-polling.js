// ============================================
// LIVE CHAT POLLING FOR USER CHATBOT
// ============================================

(function() {
    const POLLING_CONFIG = {
        INTERVAL: 5000,          // Poll every 5 seconds
        MAX_RETRIES: 3,          // Retry 3 times on error
        BACKOFF_MULTIPLIER: 1.5  // Exponential backoff
    };

    let pollingTimer = null;
    let isPollingActive = false;
    let retryCount = 0;
    let currentSessionId = null;

    // ============================================
    // START POLLING
    // ============================================
    function startLiveChatPolling(sessionId) {
        console.log('🔄 Starting live chat polling...', sessionId);
        
        // Update session ID
        currentSessionId = sessionId;
        
        // Stop any existing polling
        stopLiveChatPolling();
        
        // Start polling
        isPollingActive = true;
        retryCount = 0;
        
        // Initial check immediately
        checkForAdminResponse();
        
        // Then poll at interval
        pollingTimer = setInterval(() => {
            if (isPollingActive) {
                checkForAdminResponse();
            }
        }, POLLING_CONFIG.INTERVAL);
        
        console.log(`✅ Polling started (every ${POLLING_CONFIG.INTERVAL/1000}s)`);
    }

    // ============================================
    // STOP POLLING
    // ============================================
    function stopLiveChatPolling() {
        console.log('⏹️ Stopping live chat polling...');
        
        if (pollingTimer) {
            clearInterval(pollingTimer);
            pollingTimer = null;
        }
        
        isPollingActive = false;
        retryCount = 0;
        
        console.log('✅ Polling stopped');
    }

    // ============================================
    // CHECK FOR ADMIN RESPONSE
    // ============================================
    async function checkForAdminResponse() {
        if (!currentSessionId || !isPollingActive) {
            console.log('⏭️ Skipping poll - no active session');
            return;
        }

        try {
            console.log(`🔍 Polling for admin response... (Session: ${currentSessionId.substring(0, 8)})`);
            
            const response = await fetch(`http://127.0.0.1:5000/live-chat/pending?session_id=${currentSessionId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            // Reset retry count on success
            retryCount = 0;

            if (data.success && data.pending && data.response) {
                console.log('✅ ADMIN RESPONSE RECEIVED!');
                console.log('   Admin:', data.response.admin_name);
                console.log('   Response:', data.response.admin_response.substring(0, 50) + '...');
                
                // Display the admin response in chatbot
                displayAdminResponse(data.response);
                
                // Stop polling after receiving response
                stopLiveChatPolling();
                
                // Show notification
                showNotification('✅ Jawapan daripada admin diterima!');
                
            } else {
                console.log('⏳ No admin response yet...');
            }

        } catch (error) {
            console.error('❌ Polling error:', error);
            
            retryCount++;
            
            if (retryCount >= POLLING_CONFIG.MAX_RETRIES) {
                console.error('❌ Max retries reached, stopping polling');
                stopLiveChatPolling();
                showNotification('❌ Gagal menerima jawapan. Sila refresh halaman.', 'error');
            } else {
                console.log(`⚠️ Retry ${retryCount}/${POLLING_CONFIG.MAX_RETRIES}`);
            }
        }
    }

    // ============================================
    // DISPLAY ADMIN RESPONSE IN CHATBOT
    // ============================================
    function displayAdminResponse(responseData) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) {
            console.error('❌ Chat messages container not found');
            return;
        }

        // Create admin message bubble
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message admin-response-message';
        messageDiv.innerHTML = `
            <div class="admin-response-header">
                <span class="admin-badge">👨‍💼 ${escapeHtml(responseData.admin_name || 'Admin')}</span>
                <span class="response-time">${formatTime(responseData.updated_at)}</span>
            </div>
            <div class="admin-response-content">
                ${escapeHtml(responseData.admin_response)}
            </div>
            <div class="admin-response-footer">
                <small>✅ Dijawab oleh admin LZNK</small>
            </div>
        `;

        // Add animation
        messageDiv.style.animation = 'slideIn 0.3s ease-out';

        // Append to chat
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Play notification sound (optional)
        playNotificationSound();
    }

    // ============================================
    // SHOW NOTIFICATION
    // ============================================
    function showNotification(message, type = 'success') {
        // Check if notification already exists
        let notification = document.getElementById('livechat-notification');
        
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'livechat-notification';
            notification.className = `notification ${type}`;
            document.body.appendChild(notification);
        }

        notification.textContent = message;
        notification.className = `notification ${type} show`;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }

    // ============================================
    // HELPER FUNCTIONS
    // ============================================
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatTime(timestamp) {
        if (!timestamp) return '';
        
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('ms-MY', {
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return timestamp;
        }
    }

    function playNotificationSound() {
        try {
            // Create and play a simple notification sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (e) {
            console.log('Could not play sound:', e);
        }
    }

    // ============================================
    // EXPOSE GLOBALLY
    // ============================================
    window.LiveChatPolling = {
        start: startLiveChatPolling,
        stop: stopLiveChatPolling,
        isActive: () => isPollingActive,
        getCurrentSession: () => currentSessionId
    };

    console.log('✅ Live Chat Polling initialized');

    // ============================================
    // AUTO-START ON PAGE LOAD (if session exists)
    // ============================================
    document.addEventListener('DOMContentLoaded', () => {
        // Check if user has an active live chat session
        const sessionId = localStorage.getItem('chatbot_session_id');
        const hasActiveLiveChat = localStorage.getItem('active_livechat_request');
        
        if (sessionId && hasActiveLiveChat === 'true') {
            console.log('🔄 Resuming live chat polling for existing session...');
            startLiveChatPolling(sessionId);
        }
    });

})();

// ============================================
// CSS STYLES FOR NOTIFICATIONS AND MESSAGES
// Add to your chatbot CSS file
// ============================================
const styles = `
<style>
/* Notification styles */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    background: #10b981;
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    font-weight: 500;
    z-index: 10000;
    opacity: 0;
    transform: translateY(-20px);
    transition: all 0.3s ease;
    pointer-events: none;
}

.notification.show {
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
}

.notification.error {
    background: #ef4444;
}

/* Admin response message styles */
.admin-response-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-left: 4px solid #fbbf24;
    margin: 15px 0;
}

.admin-response-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.2);
}

.admin-badge {
    background: rgba(255,255,255,0.2);
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

.response-time {
    font-size: 11px;
    opacity: 0.8;
}

.admin-response-content {
    padding: 10px 0;
    line-height: 1.6;
    font-size: 15px;
}

.admin-response-footer {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid rgba(255,255,255,0.2);
    font-size: 12px;
    opacity: 0.9;
}

/* Slide in animation */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Polling indicator (optional) */
.polling-indicator {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: white;
    padding: 8px 15px;
    border-radius: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    font-size: 12px;
    color: #666;
    z-index: 9999;
}

.polling-indicator::before {
    content: '🔄';
    margin-right: 5px;
    animation: spin 2s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
</style>
`;

// Inject styles
if (typeof document !== 'undefined') {
    document.head.insertAdjacentHTML('beforeend', styles);
}