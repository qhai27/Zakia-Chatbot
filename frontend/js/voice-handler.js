/**
 * Voice Handler for ZAKIA Chatbot
 * Handles Speech Recognition (Voice Input) and Text-to-Speech (TTS)
 * Language: Malay (ms-MY) with Female Voice
 */

class VoiceHandler {
    constructor(chatbotInstance) {
        this.chatbot = chatbotInstance;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.isSpeaking = false;
        this.ttsEnabled = true;
        this.currentUtterance = null;
        
        // Malay language settings
        this.language = 'ms-MY';
        
        // Voice preferences
        this.preferredVoice = null;
        this.voicesLoaded = false;
        
        this.init();
    }

    init() {
        this.setupSpeechRecognition();
        this.loadVoices();
        this.createVoiceControls();
        this.loadTTSPreference();
    }

    /**
     * Load and select female Malay voice
     */
    loadVoices() {
        const setVoice = () => {
            const voices = this.synthesis.getVoices();
            
            if (voices.length === 0) {
                console.log('⏳ Voices not loaded yet, waiting...');
                return;
            }

            console.log('🔍 Available voices:', voices.map(v => `${v.name} (${v.lang})`));

            // Look for Google Bahasa Indonesia female voice specifically
            let selectedVoice = voices.find(voice => 
                voice.name === 'Google Bahasa Indonesia' || 
                voice.name.includes('Indonesian Female') ||
                voice.name.includes('id-ID')
            );

            // If not found, look for any Malay/Indonesian female voice
            if (!selectedVoice) {
                selectedVoice = voices.find(voice => 
                    (voice.lang.startsWith('ms') || voice.lang.startsWith('id')) &&
                    (voice.name.toLowerCase().includes('female') || 
                     voice.name.toLowerCase().includes('perempuan'))
                );
            }

            // If still not found, use first Malay or Indonesian voice
            if (!selectedVoice) {
                selectedVoice = voices.find(voice => 
                    voice.lang.startsWith('ms') || voice.lang.startsWith('id')
                );
            }

            // Last resort: use first available voice
            if (!selectedVoice && voices.length > 0) {
                selectedVoice = voices[0];
            }

            if (selectedVoice) {
                this.preferredVoice = selectedVoice;
                console.log('✅ Selected voice:', selectedVoice.name, `(${selectedVoice.lang})`);
                this.voicesLoaded = true;
            }
        };

        // Try to load voices immediately
        setVoice();

        // Also listen for voiceschanged event (for browsers that load voices asynchronously)
        if (this.synthesis.onvoiceschanged !== undefined) {
            this.synthesis.onvoiceschanged = setVoice;
        }

        // Fallback: try again after a delay
        setTimeout(setVoice, 100);
        setTimeout(setVoice, 500);
    }

    /**
     * Setup Web Speech API for voice input
     */
    setupSpeechRecognition() {
        // Check browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('⚠️ Speech Recognition not supported in this browser');
            // Hide mic button if not supported
            this.hideMicButtonIfNotSupported = true;
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.lang = this.language;
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.maxAlternatives = 1;

        // Mobile optimization - reduce timeout
        if (this.isMobile()) {
            console.log('📱 Mobile device detected - optimizing settings');
        }

        // Event handlers
        this.recognition.onstart = () => {
            console.log('🎤 Voice recognition started');
            this.isListening = true;
            this.updateMicButton(true);
            this.showListeningIndicator();
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('📝 Recognized text:', transcript);
            
            // Put text in input field
            this.chatbot.inputEl.value = transcript;
            
            // Trigger input event for auto-resize
            const inputEvent = new Event('input', { bubbles: true });
            this.chatbot.inputEl.dispatchEvent(inputEvent);
            
            // Auto-send after brief delay
            setTimeout(() => {
                this.chatbot.sendBtn.click();
            }, 500);
        };

        this.recognition.onerror = (event) => {
            console.error('❌ Speech recognition error:', event.error);
            this.isListening = false;
            this.updateMicButton(false);
            this.hideListeningIndicator();
            
            if (event.error === 'no-speech') {
                this.showVoiceMessage('Tiada suara dikesan. Sila cuba lagi.');
            } else if (event.error === 'not-allowed') {
                this.showVoiceMessage('Akses mikrofon ditolak. Sila benarkan akses mikrofon di tetapan pelayar.');
            } else if (event.error === 'network') {
                this.showVoiceMessage('Sambungan internet diperlukan untuk pengenalan suara.');
            } else {
                this.showVoiceMessage('Ralat pengenalan suara. Sila cuba lagi.');
            }
        };

        this.recognition.onend = () => {
            console.log('🔴 Voice recognition ended');
            this.isListening = false;
            this.updateMicButton(false);
            this.hideListeningIndicator();
        };
    }

    /**
     * Detect if running on mobile device
     */
    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    /**
     * Detect if running on iOS
     */
    isiOS() {
        return /iPhone|iPad|iPod/i.test(navigator.userAgent);
    }

    /**
     * Create voice control buttons in UI
     */
    createVoiceControls() {
        const inputArea = document.querySelector('.input-area');
        const textArea = document.getElementById('userInput');
        if (!inputArea || !textArea) return;

        // Wrap textarea in a container for positioning
        const textareaWrapper = document.createElement('div');
        textareaWrapper.className = 'textarea-wrapper';
        
        // Replace textarea with wrapper
        textArea.parentNode.insertBefore(textareaWrapper, textArea);
        textareaWrapper.appendChild(textArea);

        // Create microphone button inside textarea (only if supported)
        if (!this.hideMicButtonIfNotSupported) {
            const micButton = document.createElement('button');
            micButton.id = 'micBtn';
            micButton.className = 'btn-mic-inline';
            micButton.type = 'button';
            micButton.title = 'Tekan untuk bercakap';
            micButton.setAttribute('aria-label', 'Tekan untuk bercakap');
            micButton.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                    <line x1="12" y1="19" x2="12" y2="23"></line>
                    <line x1="8" y1="23" x2="16" y2="23"></line>
                </svg>
            `;
            micButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleListening();
            });
            
            // Add mic button to wrapper
            textareaWrapper.appendChild(micButton);
            
            // Update textarea padding to make room for mic button
            textArea.style.paddingRight = '50px';
        } else if (this.isiOS()) {
            // Show iOS helper message on first load
            setTimeout(() => {
                console.log('📱 iOS detected - Voice input not available, but TTS works!');
            }, 1000);
        }

        // Create TTS toggle button (outside textarea, before send button)
        const ttsButton = document.createElement('button');
        ttsButton.id = 'ttsBtn';
        ttsButton.className = 'btn-tts';
        ttsButton.title = 'Hidupkan/Matikan suara';
        ttsButton.setAttribute('aria-label', 'Hidupkan atau matikan suara');
        this.updateTTSButton(ttsButton);
        ttsButton.addEventListener('click', () => this.toggleTTS());

        // Insert before send button
        const sendBtn = document.getElementById('sendBtn');
        inputArea.insertBefore(ttsButton, sendBtn);

        // Add styles
        this.addVoiceStyles();
    }

    /**
     * Toggle voice listening
     */
    toggleListening() {
        if (!this.recognition) {
            // Show appropriate message based on platform
            if (this.isiOS()) {
                this.showVoiceMessage('📱 Maaf, pengenalan suara tidak disokong di iOS. Sila gunakan keyboard untuk menaip atau gunakan mikrofon keyboard iOS.');
            } else {
                this.showVoiceMessage('Pengenalan suara tidak disokong oleh pelayar ini.');
            }
            return;
        }

        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    /**
     * Start listening for voice input
     */
    startListening() {
        // Request microphone permission first on mobile
        if (this.isMobile()) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(() => {
                    console.log('✅ Microphone permission granted');
                    this.activateRecognition();
                })
                .catch((error) => {
                    console.error('❌ Microphone permission denied:', error);
                    this.showVoiceMessage('Sila benarkan akses mikrofon untuk menggunakan ciri suara.');
                });
        } else {
            this.activateRecognition();
        }
    }

    /**
     * Activate speech recognition
     */
    activateRecognition() {
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Error starting recognition:', error);
            this.showVoiceMessage('Ralat memulakan pengenalan suara.');
        }
    }

    /**
     * Stop listening
     */
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    /**
     * Update microphone button state
     */
    updateMicButton(isActive) {
        const micBtn = document.getElementById('micBtn');
        if (!micBtn) return;

        if (isActive) {
            micBtn.classList.add('active');
            micBtn.title = 'Berhenti merakam';
        } else {
            micBtn.classList.remove('active');
            micBtn.title = 'Tekan untuk bercakap';
        }
    }

    /**
     * Show listening indicator
     */
    showListeningIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'listeningIndicator';
        indicator.className = 'listening-indicator';
        indicator.innerHTML = `
            <div class="listening-pulse"></div>
            <span>Mendengar...</span>
        `;
        
        const messagesEl = this.chatbot.messagesEl;
        messagesEl.appendChild(indicator);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    /**
     * Hide listening indicator
     */
    hideListeningIndicator() {
        const indicator = document.getElementById('listeningIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Show voice message to user
     */
    showVoiceMessage(message) {
        this.chatbot.appendMessage(message, 'bot', false, { skipFeedback: true });
    }

    /**
     * Toggle Text-to-Speech
     */
    toggleTTS() {
        this.ttsEnabled = !this.ttsEnabled;
        this.saveTTSPreference();
        
        const ttsBtn = document.getElementById('ttsBtn');
        this.updateTTSButton(ttsBtn);

        // Stop current speech if TTS is disabled
        if (!this.ttsEnabled && this.isSpeaking) {
            this.stopSpeaking();
        }

        // Show feedback
        const status = this.ttsEnabled ? 'dihidupkan' : 'dimatikan';
        this.showVoiceMessage(`Suara ${status}. 🔊`);
    }

    /**
     * Update TTS button appearance
     */
    updateTTSButton(button) {
        if (!button) return;

        button.innerHTML = this.ttsEnabled ? `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
            </svg>
        ` : `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <line x1="23" y1="9" x2="17" y2="15"></line>
                <line x1="17" y1="9" x2="23" y2="15"></line>
            </svg>
        `;

        button.title = this.ttsEnabled ? 'Matikan suara' : 'Hidupkan suara';
        button.classList.toggle('active', this.ttsEnabled);
    }

    /**
     * Speak text using TTS with female Malay voice
     */
    speak(text) {
        if (!this.ttsEnabled || !text) return;

        // Reload voices if not loaded yet
        if (!this.voicesLoaded) {
            this.loadVoices();
        }

        // Stop any ongoing speech
        this.stopSpeaking();

        // Clean text for better speech
        const cleanText = this.cleanTextForSpeech(text);

        // Create utterance
        this.currentUtterance = new SpeechSynthesisUtterance(cleanText);
        this.currentUtterance.lang = this.language;
        
        // Set preferred voice (female Malay)
        if (this.preferredVoice) {
            this.currentUtterance.voice = this.preferredVoice;
            console.log('🎙️ Using voice:', this.preferredVoice.name);
        }
        
        // Voice parameters optimized for female voice - slower speed
        this.currentUtterance.rate = 0.95;  // Slower for better clarity
        this.currentUtterance.pitch = 1.1;   // Higher pitch for female voice
        this.currentUtterance.volume = 1.0;

        // Event handlers
        this.currentUtterance.onstart = () => {
            console.log('🔊 TTS started');
            this.isSpeaking = true;
            this.addSpeakingIndicator();
        };

        this.currentUtterance.onend = () => {
            console.log('🔇 TTS ended');
            this.isSpeaking = false;
            this.removeSpeakingIndicator();
            this.currentUtterance = null;
        };

        this.currentUtterance.onerror = (event) => {
            console.error('❌ TTS error:', event.error);
            this.isSpeaking = false;
            this.removeSpeakingIndicator();
        };

        // Speak
        this.synthesis.speak(this.currentUtterance);
    }

    /**
     * Stop speaking
     */
    stopSpeaking() {
        if (this.synthesis.speaking) {
            this.synthesis.cancel();
        }
        this.isSpeaking = false;
        this.removeSpeakingIndicator();
    }

    /**
     * Clean text for better speech output
     */
    cleanTextForSpeech(text) {
        let cleaned = text;
        
        // Remove HTML tags
        cleaned = cleaned.replace(/<[^>]*>/g, '');
        
        // Remove URLs
        cleaned = cleaned.replace(/https?:\/\/[^\s]+/g, '');
        
        // Remove emojis (optional - they might be spoken as descriptions)
        cleaned = cleaned.replace(/[\u{1F600}-\u{1F64F}]/gu, '');
        cleaned = cleaned.replace(/[\u{1F300}-\u{1F5FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{1F680}-\u{1F6FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{2600}-\u{26FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{2700}-\u{27BF}]/gu, '');
        
        // Replace common symbols
        cleaned = cleaned.replace(/&/g, ' dan ');
        cleaned = cleaned.replace(/@/g, ' di ');
        
        // Clean up whitespace
        cleaned = cleaned.replace(/\s+/g, ' ').trim();
        
        return cleaned;
    }

    /**
     * Add speaking indicator to last bot message
     */
    addSpeakingIndicator() {
        const messages = document.querySelectorAll('.msg.bot');
        if (messages.length === 0) return;
        
        const lastMessage = messages[messages.length - 1];
        const bubble = lastMessage.querySelector('.bot-bubble');
        
        if (bubble && !bubble.querySelector('.speaking-indicator')) {
            const indicator = document.createElement('div');
            indicator.className = 'speaking-indicator';
            indicator.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="2" y="6" width="4" height="12" rx="2">
                        <animate attributeName="height" values="12;18;12" dur="1s" repeatCount="indefinite"/>
                        <animate attributeName="y" values="6;3;6" dur="1s" repeatCount="indefinite"/>
                    </rect>
                    <rect x="10" y="4" width="4" height="16" rx="2">
                        <animate attributeName="height" values="16;20;16" dur="1s" begin="0.2s" repeatCount="indefinite"/>
                        <animate attributeName="y" values="4;2;4" dur="1s" begin="0.2s" repeatCount="indefinite"/>
                    </rect>
                    <rect x="18" y="6" width="4" height="12" rx="2">
                        <animate attributeName="height" values="12;18;12" dur="1s" begin="0.4s" repeatCount="indefinite"/>
                        <animate attributeName="y" values="6;3;6" dur="1s" begin="0.4s" repeatCount="indefinite"/>
                    </rect>
                </svg>
            `;
            bubble.appendChild(indicator);
        }
    }

    /**
     * Remove speaking indicator
     */
    removeSpeakingIndicator() {
        const indicators = document.querySelectorAll('.speaking-indicator');
        indicators.forEach(indicator => indicator.remove());
    }

    /**
     * Save TTS preference to localStorage
     */
    saveTTSPreference() {
        try {
            localStorage.setItem('zakia_tts_enabled', this.ttsEnabled ? '1' : '0');
        } catch (e) {
            console.warn('Could not save TTS preference:', e);
        }
    }

    /**
     * Load TTS preference from localStorage
     */
    loadTTSPreference() {
        try {
            const saved = localStorage.getItem('zakia_tts_enabled');
            if (saved !== null) {
                this.ttsEnabled = saved === '1';
                const ttsBtn = document.getElementById('ttsBtn');
                if (ttsBtn) {
                    this.updateTTSButton(ttsBtn);
                }
            }
        } catch (e) {
            console.warn('Could not load TTS preference:', e);
        }
    }

    /**
     * Add CSS styles for voice controls
     */
    addVoiceStyles() {
        if (document.getElementById('voice-handler-styles')) return;

        const style = document.createElement('style');
        style.id = 'voice-handler-styles';
        style.textContent = `
            /* Textarea wrapper for positioning mic button */
            .textarea-wrapper {
                position: relative;
                flex: 1;
                display: flex;
                align-items: flex-end;
            }

            .textarea-wrapper textarea {
                flex: 1;
                width: 100%;
            }

            /* Inline mic button inside textarea */
            .btn-mic-inline {
                position: absolute;
                right: 8px;
                bottom: 8px;
                background: transparent;
                border: none;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
                color: #157347;
                flex-shrink: 0;
                z-index: 10;
                padding: 0;
            }

            .btn-mic-inline:hover {
                background: rgba(21, 115, 71, 0.1);
                transform: scale(1.1);
            }

            .btn-mic-inline:active {
                transform: scale(0.95);
            }

            .btn-mic-inline.active {
                background: #FF5252;
                color: white;
                animation: pulse-mic 1.5s infinite;
            }

            .btn-mic-inline svg {
                width: 20px;
                height: 20px;
            }

            /* TTS button (external) */
            .btn-tts {
                background: transparent;
                border: none;
                width: 44px;
                height: 44px;
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
                color: #157347;
                flex-shrink: 0;
            }

            .btn-tts:hover {
                background: rgba(21, 115, 71, 0.1);
                transform: scale(1.1);
            }

            .btn-tts:active {
                transform: scale(0.95);
            }

            .btn-tts.active {
                color: #157347;
            }

            @keyframes pulse-mic {
                0%, 100% {
                    box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7);
                }
                50% {
                    box-shadow: 0 0 0 10px rgba(255, 82, 82, 0);
                }
            }

            .listening-indicator {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 12px 16px;
                margin: 8px 0;
                background: linear-gradient(135deg, #FFF3CD 0%, #FFE69C 100%);
                border-radius: 12px;
                border-left: 4px solid #FF5252;
                animation: fadeIn 0.3s ease;
            }

            .listening-pulse {
                width: 20px;
                height: 20px;
                background: #FF5252;
                border-radius: 50%;
                animation: pulse-listening 1s infinite;
            }

            @keyframes pulse-listening {
                0%, 100% {
                    transform: scale(1);
                    opacity: 1;
                }
                50% {
                    transform: scale(1.2);
                    opacity: 0.7;
                }
            }

            .listening-indicator span {
                font-weight: 600;
                color: #856404;
                font-size: 14px;
            }

            .speaking-indicator {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                margin-left: 8px;
                padding: 4px 8px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.9);
            }

            @keyframes fadeIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            /* Mobile optimizations */
            @media (max-width: 480px) {
                .btn-mic-inline {
                    width: 32px;
                    height: 32px;
                    right: 6px;
                    bottom: 6px;
                }
                
                .btn-mic-inline svg {
                    width: 18px;
                    height: 18px;
                }

                .btn-tts {
                    width: 40px;
                    height: 40px;
                }
                
                .btn-tts svg {
                    width: 20px;
                    height: 20px;
                }
                
                .listening-indicator {
                    padding: 10px 12px;
                    font-size: 13px;
                }
                
                .listening-pulse {
                    width: 16px;
                    height: 16px;
                }

                /* Adjust textarea padding for smaller mic button */
                .textarea-wrapper textarea {
                    padding-right: 45px !important;
                }
            }

            /* Extra small screens */
            @media (max-width: 375px) {
                .btn-mic-inline {
                    width: 30px;
                    height: 30px;
                }
                
                .btn-mic-inline svg {
                    width: 16px;
                    height: 16px;
                }

                .textarea-wrapper textarea {
                    padding-right: 40px !important;
                }
            }

            /* Prevent text selection on buttons (mobile) */
            .btn-mic-inline, .btn-tts {
                -webkit-tap-highlight-color: transparent;
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                user-select: none;
            }

            /* Better touch feedback on mobile */
            @media (hover: none) and (pointer: coarse) {
                .btn-mic-inline:active, .btn-tts:active {
                    background: rgba(21, 115, 71, 0.15);
                }
            }

            /* Ensure mic button stays visible when textarea grows */
            .textarea-wrapper {
                position: relative;
            }

            .textarea-wrapper .btn-mic-inline {
                position: absolute;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Auto-speak bot messages
     */
    handleBotMessage(text) {
        if (this.ttsEnabled && text) {
            // Small delay before speaking
            setTimeout(() => {
                this.speak(text);
            }, 300);
        }
    }
}

// Export for use in chatbot
window.VoiceHandler = VoiceHandler;