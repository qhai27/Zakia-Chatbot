/**
 * Voice Handler for ZAKIA Chatbot - Hybrid Edition
 * STT: Web Speech API (Malay - Malaysia)
 * TTS: ElevenLabs API (Bahasa Melayu Female Voice)
 */

class VoiceHandler {
    constructor(chatbotInstance) {
        this.chatbot = chatbotInstance;
        this.recognition = null;
        this.isListening = false;
        this.isSpeaking = false;
        this.ttsEnabled = true;
        
        // Malay language settings for STT
        this.recognitionLanguage = 'ms-MY'; // Malay - Malaysia
        
        // ElevenLabs Configuration for TTS
        this.elevenLabsApiKey = '4a1b1788fb59eecefda5cf2e4690da16ab397d626b9805cd3174b0995a028613'; //ID key 
        this.elevenLabsVoiceId = 'F9yCRElGuNvX7A2kGbWz'; // Maya J 
        this.elevenLabsModelId = 'eleven_multilingual_v2'; // Supports Bahasa Melayu
        
        // Audio handling
        this.currentAudio = null;
        
        this.init();
    }

    init() {
        this.setupSpeechRecognition();
        this.createVoiceControls();
        this.loadTTSPreference();
    }

    /**
     * Set ElevenLabs API Key
     */
    setApiKey(apiKey) {
        this.elevenLabsApiKey = apiKey;
        console.log('ElevenLabs API Key set');
    }

    /**
     * Set ElevenLabs Voice ID (optional customization)
     */
    setVoiceId(voiceId) {
        this.elevenLabsVoiceId = voiceId;
        console.log('ElevenLabs Voice ID updated:', voiceId);
    }

    /**
     * Setup Web Speech API for voice input (Malay - Malaysia)
     */
    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('⚠️ Speech Recognition not supported in this browser');
            this.hideMicButtonIfNotSupported = true;
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.lang = this.recognitionLanguage; // ms-MY
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.maxAlternatives = 1;

        if (this.isMobile()) {
            console.log('📱 Peranti mudah alih dikesan');
        }

        this.recognition.onstart = () => {
            console.log('🎤 Pengenalan suara dimulakan');
            this.isListening = true;
            this.updateMicButton(true);
            this.showListeningIndicator();
        };

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('📝 Teks dikenali:', transcript);
            
            this.chatbot.inputEl.value = transcript;
            
            const inputEvent = new Event('input', { bubbles: true });
            this.chatbot.inputEl.dispatchEvent(inputEvent);
            
            setTimeout(() => {
                this.chatbot.sendBtn.click();
            }, 500);
        };

        this.recognition.onerror = (event) => {
            console.error('❌ Ralat pengenalan suara:', event.error);
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
            console.log('🔴 Pengenalan suara ditamatkan');
            this.isListening = false;
            this.updateMicButton(false);
            this.hideListeningIndicator();
        };
    }

    isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    isiOS() {
        return /iPhone|iPad|iPod/i.test(navigator.userAgent);
    }

    createVoiceControls() {
        const inputArea = document.querySelector('.input-area');
        const textArea = document.getElementById('userInput');
        if (!inputArea || !textArea) return;

        const textareaWrapper = document.createElement('div');
        textareaWrapper.className = 'textarea-wrapper';
        
        textArea.parentNode.insertBefore(textareaWrapper, textArea);
        textareaWrapper.appendChild(textArea);

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
            
            textareaWrapper.appendChild(micButton);
            textArea.style.paddingRight = '50px';
        }

        const ttsButton = document.createElement('button');
        ttsButton.id = 'ttsBtn';
        ttsButton.className = 'btn-tts';
        ttsButton.title = 'Hidupkan/Matikan suara';
        ttsButton.setAttribute('aria-label', 'Hidupkan atau matikan suara');
        this.updateTTSButton(ttsButton);
        ttsButton.addEventListener('click', () => this.toggleTTS());

        const sendBtn = document.getElementById('sendBtn');
        inputArea.insertBefore(ttsButton, sendBtn);

        this.addVoiceStyles();
    }

    toggleListening() {
        if (!this.recognition) {
            if (this.isiOS()) {
                this.showVoiceMessage('📱 Maaf, pengenalan suara tidak disokong di iOS. Sila gunakan keyboard untuk menaip.');
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

    startListening() {
        if (this.isMobile()) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(() => {
                    console.log('✅ Kebenaran mikrofon diberikan');
                    this.activateRecognition();
                })
                .catch((error) => {
                    console.error('❌ Kebenaran mikrofon ditolak:', error);
                    this.showVoiceMessage('Sila benarkan akses mikrofon untuk menggunakan ciri suara.');
                });
        } else {
            this.activateRecognition();
        }
    }

    activateRecognition() {
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Ralat memulakan pengenalan:', error);
            this.showVoiceMessage('Ralat memulakan pengenalan suara.');
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

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

    hideListeningIndicator() {
        const indicator = document.getElementById('listeningIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    showVoiceMessage(message) {
        this.chatbot.appendMessage(message, 'bot', false, { skipFeedback: true });
    }

    toggleTTS() {
        this.ttsEnabled = !this.ttsEnabled;
        this.saveTTSPreference();
        
        const ttsBtn = document.getElementById('ttsBtn');
        this.updateTTSButton(ttsBtn);

        if (!this.ttsEnabled && this.isSpeaking) {
            this.stopSpeaking();
        }

        const status = this.ttsEnabled ? 'dihidupkan' : 'dimatikan';
        this.showVoiceMessage(`Suara ${status}. 🔊`);
    }

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
     * Speak text using ElevenLabs Text-to-Speech API (Bahasa Melayu Female Voice)
     */
    async speak(text) {
        if (!this.ttsEnabled || !text) return;
        
        if (!this.elevenLabsApiKey) {
            console.warn('⚠️ API Key ElevenLabs belum ditetapkan');
            return;
        }

        // Stop any ongoing speech
        this.stopSpeaking();

        // Clean text for better speech
        const cleanText = this.cleanTextForSpeech(text);
        
        if (!cleanText) return;

        try {
            this.isSpeaking = true;
            this.addSpeakingIndicator();
            
            console.log('🎙️ Menghantar ke ElevenLabs TTS...');
            
            // Call ElevenLabs TTS API
            const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${this.elevenLabsVoiceId}`, {
                method: 'POST',
                headers: {
                    'Accept': 'audio/mpeg',
                    'Content-Type': 'application/json',
                    'xi-api-key': this.elevenLabsApiKey
                },
                body: JSON.stringify({
                    text: cleanText,
                    model_id: this.elevenLabsModelId,
                    voice_settings: {
                        stability: 0.5,
                        similarity_boost: 0.75,
                        style: 0.0,
                        use_speaker_boost: true
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`ElevenLabs TTS Error: ${response.status}`);
            }
            
            // Get audio blob
            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Play audio
            this.currentAudio = new Audio(audioUrl);
            
            this.currentAudio.onended = () => {
                console.log('🔇 TTS ditamatkan');
                this.isSpeaking = false;
                this.removeSpeakingIndicator();
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
            };
            
            this.currentAudio.onerror = (error) => {
                console.error('❌ Ralat audio:', error);
                this.isSpeaking = false;
                this.removeSpeakingIndicator();
                URL.revokeObjectURL(audioUrl);
            };
            
            await this.currentAudio.play();
            console.log('🔊 TTS dimainkan');
            
        } catch (error) {
            console.error('❌ Ralat ElevenLabs TTS:', error);
            this.isSpeaking = false;
            this.removeSpeakingIndicator();
        }
    }

    stopSpeaking() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
        }
        this.isSpeaking = false;
        this.removeSpeakingIndicator();
    }

    cleanTextForSpeech(text) {
        let cleaned = text;
        
        // Remove HTML tags
        cleaned = cleaned.replace(/<[^>]*>/g, '');
        
        // Remove URLs
        cleaned = cleaned.replace(/https?:\/\/[^\s]+/g, '');
        
        // Remove emojis
        cleaned = cleaned.replace(/[\u{1F600}-\u{1F64F}]/gu, '');
        cleaned = cleaned.replace(/[\u{1F300}-\u{1F5FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{1F680}-\u{1F6FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{2600}-\u{26FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{2700}-\u{27BF}]/gu, '');
        
        // Replace symbols with Malay words
        cleaned = cleaned.replace(/&/g, ' dan ');
        cleaned = cleaned.replace(/@/g, ' di ');
        cleaned = cleaned.replace(/%/g, ' peratus ');
        cleaned = cleaned.replace(/\+/g, ' tambah ');
        cleaned = cleaned.replace(/-/g, ' ');
        
        // Clean whitespace
        cleaned = cleaned.replace(/\s+/g, ' ').trim();

        // Remove remaining special characters but keep letters, numbers, and basic punctuation
        cleaned = cleaned.replace(/[^a-zA-Z0-9\s,.!?'-]/g, ' ');
        
        // Clean up multiple spaces and trim
        cleaned = cleaned.replace(/\s+/g, ' ').trim();
        
        return cleaned;
    }

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

    removeSpeakingIndicator() {
        const indicators = document.querySelectorAll('.speaking-indicator');
        indicators.forEach(indicator => indicator.remove());
    }

    saveTTSPreference() {
        try {
            localStorage.setItem('zakia_tts_enabled', this.ttsEnabled ? '1' : '0');
        } catch (e) {
            console.warn('Tidak dapat menyimpan keutamaan TTS:', e);
        }
    }

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
            console.warn('Tidak dapat memuatkan keutamaan TTS:', e);
        }
    }

    addVoiceStyles() {
        if (document.getElementById('voice-handler-styles')) return;

        const style = document.createElement('style');
        style.id = 'voice-handler-styles';
        style.textContent = `
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

                .textarea-wrapper textarea {
                    padding-right: 45px !important;
                }
            }

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

            .btn-mic-inline, .btn-tts {
                -webkit-tap-highlight-color: transparent;
                -webkit-touch-callout: none;
                -webkit-user-select: none;
                user-select: none;
            }

            @media (hover: none) and (pointer: coarse) {
                .btn-mic-inline:active, .btn-tts:active {
                    background: rgba(21, 115, 71, 0.15);
                }
            }

            .textarea-wrapper {
                position: relative;
            }

            .textarea-wrapper .btn-mic-inline {
                position: absolute;
            }
        `;
        document.head.appendChild(style);
    }

    handleBotMessage(text) {
        if (this.ttsEnabled && text) {
            setTimeout(() => {
                this.speak(text);
            }, 300);
        }
    }
}

window.VoiceHandler = VoiceHandler;