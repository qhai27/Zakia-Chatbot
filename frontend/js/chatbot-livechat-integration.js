// ============================================
// INTEGRATE LIVE CHAT POLLING INTO CHATBOT
// ============================================

// When user clicks "Bercakap dengan Admin"
async function escalateLiveChat() {
    const userMessage = document.getElementById('userInput').value.trim();
    const lastBotResponse = getLastBotResponse(); // Get last bot message
    
    if (!userMessage) {
        alert('Sila taip soalan anda terlebih dahulu.');
        return;
    }

    try {
        // Show loading
        showLoadingMessage('⏳ Menghantar permintaan kepada admin...');

        // Send escalation request
        const response = await fetch('http://127.0.0.1:5000/live-chat/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                user_message: userMessage,
                bot_response: lastBotResponse
            })
        });

        const data = await response.json();

        if (data.success) {
            // Display confirmation message
            displayMessage('✅ Permintaan anda telah dihantar kepada admin. Sila tunggu sebentar...', 'bot');
            
            // ⭐ START POLLING FOR ADMIN RESPONSE ⭐
            console.log('🔄 Starting live chat polling...');
            window.LiveChatPolling.start(sessionId);
            
            // Store active live chat status
            localStorage.setItem('active_livechat_request', 'true');
            localStorage.setItem('chatbot_session_id', sessionId);
            
            // Show polling indicator (optional)
            showPollingIndicator();
            
            // Clear input
            document.getElementById('userInput').value = '';
            
        } else {
            throw new Error(data.error || 'Failed to escalate');
        }

    } catch (error) {
        console.error('❌ Escalation error:', error);
        displayMessage('❌ Maaf, gagal menghantar permintaan. Sila cuba lagi.', 'bot');
    }
}

// ============================================
// SHOW POLLING INDICATOR
// ============================================
function showPollingIndicator() {
    // Remove existing indicator
    const existing = document.getElementById('polling-indicator');
    if (existing) {
        existing.remove();
    }

    // Create new indicator
    const indicator = document.createElement('div');
    indicator.id = 'polling-indicator';
    indicator.className = 'polling-indicator';
    indicator.innerHTML = '⏳ Menunggu jawapan admin...';
    document.body.appendChild(indicator);
}

// ============================================
// HIDE POLLING INDICATOR
// ============================================
function hidePollingIndicator() {
    const indicator = document.getElementById('polling-indicator');
    if (indicator) {
        indicator.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => indicator.remove(), 300);
    }
}

// ============================================
// HELPER: GET LAST BOT RESPONSE
// ============================================
function getLastBotResponse() {
    const botMessages = document.querySelectorAll('.bot-message');
    if (botMessages.length > 0) {
        const lastMessage = botMessages[botMessages.length - 1];
        return lastMessage.textContent.trim();
    }
    return 'No previous bot response';
}

// ============================================
// HELPER: DISPLAY MESSAGE
// ============================================
function displayMessage(text, sender = 'bot') {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.textContent = text;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============================================
// HELPER: SHOW LOADING
// ============================================
function showLoadingMessage(text) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    // Remove existing loading
    const existingLoading = chatMessages.querySelector('.loading-message');
    if (existingLoading) {
        existingLoading.remove();
    }

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message loading-message';
    loadingDiv.innerHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <span>${text}</span>
    `;
    
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============================================
// OVERRIDE displayAdminResponse in polling script
// Make sure it integrates with your chatbot UI
// ============================================
window.displayAdminResponse = function(responseData) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) {
        console.error('❌ Chat messages container not found');
        return;
    }

    // Remove loading messages
    const loadingMessages = chatMessages.querySelectorAll('.loading-message');
    loadingMessages.forEach(msg => msg.remove());

    // Create admin response message
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message admin-response-message';
    messageDiv.innerHTML = `
        <div class="admin-response-header">
            <span class="admin-badge">👨‍💼 ${escapeHtml(responseData.admin_name || 'Admin LZNK')}</span>
            <span class="response-time">${formatTime(responseData.updated_at)}</span>
        </div>
        <div class="admin-response-content">
            ${escapeHtml(responseData.admin_response)}
        </div>
        <div class="admin-response-footer">
            <small>✅ Dijawab oleh staf LZNK</small>
        </div>
    `;

    // Add animation
    messageDiv.style.animation = 'slideIn 0.3s ease-out';

    // Append to chat
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Hide polling indicator
    hidePollingIndicator();

    // Clear active live chat status
    localStorage.removeItem('active_livechat_request');

    // Play notification sound
    playNotificationSound();
};

// ============================================
// STOP POLLING ON CHAT CLOSE
// ============================================
window.addEventListener('beforeunload', () => {
    if (window.LiveChatPolling && window.LiveChatPolling.isActive()) {
        console.log('⏹️ Stopping polling before page unload');
        window.LiveChatPolling.stop();
    }
});

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
// CSS FOR LOADING ANIMATION
// ============================================
const loadingStyles = `
<style>
.loading-message {
    display: flex;
    align-items: center;
    gap: 10px;
    opacity: 0.8;
}

.loading-dots {
    display: flex;
    gap: 4px;
}

.loading-dots span {
    width: 8px;
    height: 8px;
    background: currentColor;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
    animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
    animation-delay: -0.16s;
}

@keyframes bounce {
    0%, 80%, 100% {
        transform: scale(0);
    }
    40% {
        transform: scale(1);
    }
}

@keyframes fadeOut {
    from {
        opacity: 1;
        transform: translateY(0);
    }
    to {
        opacity: 0;
        transform: translateY(10px);
    }
}
</style>
`;

// Inject styles
if (typeof document !== 'undefined') {
    document.head.insertAdjacentHTML('beforeend', loadingStyles);
}

console.log('✅ Live Chat integration initialized');