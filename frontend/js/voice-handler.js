/**
 * Voice Handler for ZAKIA Chatbot - Hybrid Edition
 * STT: Web Speech API (Malay - Malaysia)
 * TTS: Google Cloud Text-to-Speech API (Chirp3-HD - Bahasa Melayu)
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
        
        // Google Cloud TTS Configuration (Chirp3-HD)
        this.googleApiKey = ''; // Google Cloud API Key
        this.googleTtsEndpoint = 'https://texttospeech.googleapis.com/v1/text:synthesize';
        
        // Chirp3-HD voice for Bahasa Melayu
        this.voiceName = 'ms-MY-Standard-C'; // Default: Female voice
        this.languageCode = 'ms-MY';
        
        // Audio handling
        this.currentAudio = null;
        this.speechAbortController = null;
        
        this.init();
    }

    init() {
        this.setupSpeechRecognition();
        this.createVoiceControls();
        this.loadTTSPreference();
    }

    /**
     * Set Google Cloud API Key
     */
    setApiKey(apiKey) {
        this.googleApiKey = apiKey;
        console.log('Google Cloud API Key set');
    }

    /**
     * Set Google Cloud TTS Voice Name
     */
    setVoiceId(voiceName) {
        this.voiceName = voiceName;
        console.log('Google Cloud Voice updated:', voiceName);
    }

    /**
     * Convert numbers to Malay words
     */
    numberToMalayWords(num) {
        const ones = ['', 'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh', 'lapan', 'sembilan'];
        const teens = ['sepuluh', 'sebelas', 'dua belas', 'tiga belas', 'empat belas', 'lima belas', 
                       'enam belas', 'tujuh belas', 'lapan belas', 'sembilan belas'];
        
        if (num === 0) return 'kosong';
        if (num < 10) return ones[num];
        if (num >= 10 && num < 20) return teens[num - 10];
        if (num >= 20 && num < 100) {
            const tens = Math.floor(num / 10);
            const remainder = num % 10;
            return ones[tens] + ' puluh' + (remainder ? ' ' + ones[remainder] : '');
        }
        if (num >= 100 && num < 1000) {
            const hundreds = Math.floor(num / 100);
            const remainder = num % 100;
            const hundredWord = hundreds === 1 ? 'seratus' : ones[hundreds] + ' ratus';
            return hundredWord + (remainder ? ' ' + this.numberToMalayWords(remainder) : '');
        }
        if (num >= 1000 && num < 1000000) {
            const thousands = Math.floor(num / 1000);
            const remainder = num % 1000;
            const thousandWord = thousands === 1 ? 'seribu' : this.numberToMalayWords(thousands) + ' ribu';
            return thousandWord + (remainder ? ' ' + this.numberToMalayWords(remainder) : '');
        }
        if (num >= 1000000 && num < 1000000000) {
            const millions = Math.floor(num / 1000000);
            const remainder = num % 1000000;
            return this.numberToMalayWords(millions) + ' juta' + (remainder ? ' ' + this.numberToMalayWords(remainder) : '');
        }
        
        return num.toString();
    }

    /**
     * Setup Web Speech API for voice input (Malay - Malaysia)
     */
    setupSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('⚠️ Speech Recognition not supported in this browser');
            this.hideMicButtonIfNotSupported = true;
         }

        this.recognition = new SpeechRecognition();
        this.recognition.lang = this.recognitionLanguage;
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
     * Speak text using Google Cloud Text-to-Speech API
     */
    async speak(text) {
        if (!this.ttsEnabled || !text) return;
        
        if (!this.googleApiKey) {
            console.warn('⚠️ Google Cloud API Key belum ditetapkan');
            return;
        }

        // Abort any previous network request for TTS
        if (this.speechAbortController) {
            this.speechAbortController.abort();
            this.speechAbortController = null;
        }

        // Stop any audio currently playing
        this.stopSpeaking();

        // Clean text for better speech
        const cleanText = this.cleanTextForSpeech(text);
        
        if (!cleanText) return;

        // Prepare a fresh abort controller for this request
        this.speechAbortController = new AbortController();
        const signal = this.speechAbortController.signal;
        const myController = this.speechAbortController;

        try {
            this.isSpeaking = true;

            // Delay indicator slightly to ensure bot bubble is in the DOM
            setTimeout(() => {
                if (this.isSpeaking) this.addSpeakingIndicator();
            }, 100);
            
            console.log('🎙️ Menghantar ke Google Cloud TTS...');
            console.log('📝 Teks selepas dibersihkan:', cleanText);
            
            // Call Google Cloud TTS API
            const response = await fetch(
                `${this.googleTtsEndpoint}?key=${this.googleApiKey}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        input: {
                            text: cleanText
                        },
                        voice: {
                            languageCode: this.languageCode,
                            name: this.voiceName
                        },
                        audioConfig: {
                            audioEncoding: 'MP3',
                            speakingRate: 1.0,
                            pitch: 0.0,
                            volumeGainDb: 0.0
                        }
                    }),
                    signal
                }
            );
            
            if (!response.ok) {
                const errBody = await response.text();
                throw new Error(`Google Cloud TTS Error ${response.status}: ${errBody}`);
            }

            if (signal.aborted) {
                console.log('🔇 TTS request was aborted before receiving audio');
                return;
            }

            // Google returns base64-encoded audio in JSON
            const data = await response.json();
            const audioContent = data.audioContent;
            
            if (!audioContent) {
                throw new Error('Tiada kandungan audio diterima dari Google TTS');
            }

            // Decode base64 → Blob → Object URL
            const byteCharacters = atob(audioContent);
            const byteNumbers = new Uint8Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const audioBlob = new Blob([byteNumbers], { type: 'audio/mpeg' });
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
            if (error.name === 'AbortError') {
                console.log('🔇 TTS fetch aborted');
            } else {
                console.error('❌ Ralat Google Cloud TTS:', error);
            }
            this.isSpeaking = false;
            this.removeSpeakingIndicator();
        } finally {
            if (this.speechAbortController === myController) {
                this.speechAbortController = null;
            }
        }
    }

    stopSpeaking() {
        if (this.speechAbortController) {
            this.speechAbortController.abort();
            this.speechAbortController = null;
        }

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
        
        cleaned = cleaned.replace(/<[^>]*>/g, '');
        cleaned = cleaned.replace(/https?:\/\/[^\s]+/g, '');
        cleaned = cleaned.replace(/[\u{1F600}-\u{1F64F}]/gu, '');
        cleaned = cleaned.replace(/[\u{1F300}-\u{1F5FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{1F680}-\u{1F6FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{2600}-\u{26FF}]/gu, '');
        cleaned = cleaned.replace(/[\u{2700}-\u{27BF}]/gu, '');
        
        cleaned = cleaned.replace(/rm\s*([\d,]+)/gi, (match, digits) => {
            const value = parseInt(digits.replace(/,/g, ''), 10);
            if (isNaN(value)) return match;
            return 'rm ' + this.numberToMalayWords(value);
        });

        cleaned = cleaned.replace(/(\d+)\.(\d+)%/g, (match, whole, decimal) => {
            const wholePart = this.numberToMalayWords(parseInt(whole));
            const decimalParts = decimal.split('').map(d => this.numberToMalayWords(parseInt(d))).join(' ');
            return wholePart + ' point ' + decimalParts + ' peratus';
        });
        
        cleaned = cleaned.replace(/(\d+)%/g, (match, num) => {
            return this.numberToMalayWords(parseInt(num)) + ' peratus';
        });
        
        cleaned = cleaned.replace(/(\d+)\.(\d+)/g, (match, whole, decimal) => {
            const wholePart = this.numberToMalayWords(parseInt(whole));
            const decimalParts = decimal.split('').map(d => this.numberToMalayWords(parseInt(d))).join(' ');
            return wholePart + ' point ' + decimalParts;
        });
        
        cleaned = cleaned.replace(/\b(\d+)\b/g, (match, num) => {
            return this.numberToMalayWords(parseInt(num));
        });
        
        cleaned = cleaned.replace(/&/g, ' dan ');
        cleaned = cleaned.replace(/@/g, ' di ');
        cleaned = cleaned.replace(/\+/g, ' tambah ');
        cleaned = cleaned.replace(/\$/g, ' dolar ');
        cleaned = cleaned.replace(/RM/g, ' ringgit ');
        cleaned = cleaned.replace(/\n\n+/g, ', ');
        cleaned = cleaned.replace(/\n/g, ', ');
        cleaned = cleaned.replace(/\.([A-Z])/g, '. $1');
        cleaned = cleaned.replace(/:/g, ', ');
        cleaned = cleaned.replace(/[•\-\*]\s*/g, ', ');
        cleaned = cleaned.replace(/\s*[-–—]\s*/g, ', ');
        cleaned = cleaned.replace(/\s+/g, ' ').trim();
        cleaned = cleaned.replace(/[^a-zA-Z\s,.!?'-]/g, ' ');
        cleaned = cleaned.replace(/,+/g, ',');
        cleaned = cleaned.replace(/\s*,\s*/g, ', ');
        cleaned = cleaned.replace(/\s+/g, ' ').trim();
        cleaned = cleaned.replace(/^,\s*|,\s*$/g, '');
        
        return cleaned;
    }

    /**
     * Add speaking indicator to the last bot bubble.
     * Retries up to 15 times (750ms) to handle cases where the
     * bubble hasn't rendered in the DOM yet when speak() is called.
     */
    addSpeakingIndicator() {
        this._tryAddSpeakingIndicator(0);
    }

    _tryAddSpeakingIndicator(attempt) {
        if (attempt > 20) {
            console.warn('⚠️ Speaking indicator: could not find .bubble.bot-bubble after 20 attempts');
            return;
        }

        // Direct selector — the bubble is <div class="bubble bot-bubble">
        const all = document.querySelectorAll('.bubble.bot-bubble');
        if (!all || all.length === 0) {
            setTimeout(() => this._tryAddSpeakingIndicator(attempt + 1), 50);
            return;
        }

        const bubble = all[all.length - 1]; // last bot bubble

        // Don't add twice
        if (bubble.querySelector('.speaking-indicator')) return;

        const indicator = document.createElement('span');
        indicator.className = 'speaking-indicator';
        indicator.setAttribute('aria-label', 'Sedang bercakap');
        indicator.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:middle;">
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
        console.log('🔊 Speaking indicator added to .bubble.bot-bubble');
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
                0%, 100% { box-shadow: 0 0 0 0 rgba(255, 82, 82, 0.7); }
                50% { box-shadow: 0 0 0 10px rgba(255, 82, 82, 0); }
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
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.7; }
            }

            .listening-indicator span {
                font-weight: 600;
                color: #856404;
                font-size: 14px;
            }

            /* Speaking indicator — visible on both light and dark bubbles */
            .speaking-indicator {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                margin-left: 8px;
                padding: 3px 7px;
                background: rgba(21, 115, 71, 0.15);
                border-radius: 20px;
                vertical-align: middle;
                animation: fadeIn 0.2s ease;
            }

            .speaking-indicator svg {
                color: #f7fffb;
                fill: #f2f4f3;
            }

            /* If the bubble has a dark/green background, use white icons */
            .bot-bubble .speaking-indicator svg,
            .bubble .speaking-indicator svg {
                fill: currentColor;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to   { opacity: 1; transform: translateY(0); }
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
            // Debounce: cancel any pending speak call within 200ms to prevent double-fire
            if (this._speakDebounceTimer) {
                clearTimeout(this._speakDebounceTimer);
            }
            this._lastSpeakText = text;
            this._speakDebounceTimer = setTimeout(() => {
                this._speakDebounceTimer = null;
                if (this._lastSpeakText) {
                    this.speak(this._lastSpeakText);
                    this._lastSpeakText = null;
                }
            }, 150);
        }
    }
}

window.VoiceHandler = VoiceHandler;
