// ============================================
// CONFIGURATION FILE - UPDATED
// ============================================

window.CONFIG = {
    // API Configuration
    API_BASE_URL: 'http://127.0.0.1:5000',
    
    // API Endpoints
    ENDPOINTS: {
        CHAT: '/chat',
        FAQS: '/faqs',
        CONTACT_REQUEST: '/contact-request', 
        ZAKAT_NISAB: '/zakat/nisab',
        ZAKAT_CALCULATE: '/zakat/calculate'
    },
    
    // UI Settings
    UI: {
        TYPING_DELAY: 1000,
        QUICK_REPLY_SELECTION_DURATION: 300
    },
    
    // Messages
    MESSAGES: {
        SESSION_ENDED: 'Terima kasih kerana menggunakan ZAKIA. Jika ada soalan lain, jangan segan untuk bertanya! 😊',
        SERVER_ERROR: 'Maaf, ada masalah pada server. Sila cuba lagi.',
        CONNECTION_ERROR: 'Maaf, ada masalah sambungan. Sila cuba lagi.'
    },
    
    // Office Hours (for reference)
    OFFICE_HOURS: {
        SUNDAY: { open: '09:00', close: '17:00' },
        MONDAY: { open: '09:00', close: '17:00' },
        TUESDAY: { open: '09:00', close: '17:00' },
        WEDNESDAY: { open: '09:00', close: '17:00' },
        THURSDAY: { open: '09:00', close: '15:30' },
        FRIDAY: { closed: true },
        SATURDAY: { closed: true }
    }
};